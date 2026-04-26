"""OCR extractor — PaddleOCR with PP-StructureV2.

Used for:
  - Scanned PDFs (pages rendered to images by pdf_extractor.render_pages_as_images)
  - Direct image uploads (JPG, PNG, TIFF, WEBP)

PP-StructureV2 returns structured table output with per-cell bounding boxes and
confidence scores — not a wall of text. This is what enables the visual grounding
feature where the frontend highlights source regions on hover.

Language: French (fr) + Arabic (ar). Models handle mixed-language documents.

Tiered user validation based on confidence (enforced in the router/frontend):
  ≥ 90%  → pre-populate, green, no active confirmation needed
  60–90% → pre-populate, yellow, user must acknowledge/correct
  < 60%  → do not auto-populate; show raw OCR output + highlighted region
  not detected → empty field; required fields flagged

PROTOTYPE ONLY: PaddleOCR PP-StructureV2 is the specified OCR engine.
Confidence scores and bounding boxes are stored alongside every value.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from backend.services.ingestion_service.extractors.base import BoundingBox, ExtractionResult

_PADDLE_INITIALIZED = False
_STRUCTURE_ENGINE = None


def _get_structure_engine():
    global _PADDLE_INITIALIZED, _STRUCTURE_ENGINE
    if not _PADDLE_INITIALIZED:
        from paddleocr import PPStructure  # deferred — large import

        _STRUCTURE_ENGINE = PPStructure(
            lang="fr",           # French primary; Arabic detected automatically by PP-StructureV2
            show_log=False,
            table=True,          # enable table structure recognition
            layout=True,         # enable layout analysis
        )
        _PADDLE_INITIALIZED = True
    return _STRUCTURE_ENGINE


def preprocess_image(image_bytes: bytes, min_dpi: int = 150) -> tuple[np.ndarray, float]:
    """Convert raw bytes → preprocessed numpy array for OCR.

    Returns (array, estimated_dpi). Raises ValueError if DPI is below threshold.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Estimate DPI from image metadata
    dpi_info = img.info.get("dpi", (72, 72))
    estimated_dpi = float(dpi_info[0]) if isinstance(dpi_info, tuple) else float(dpi_info)

    if estimated_dpi < min_dpi:
        from backend.shared.exceptions import ImageResolutionTooLow
        raise ImageResolutionTooLow(
            detail=f"Estimated DPI: {estimated_dpi:.0f}. Minimum required: {min_dpi}."
        )

    # Grayscale + contrast enhancement + mild sharpen
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = img.filter(ImageFilter.SHARPEN)

    return np.array(img), estimated_dpi


def extract_from_image_bytes(image_bytes: bytes) -> ExtractionResult:
    """Run PP-StructureV2 on a single image and return ExtractionResult."""
    arr, _ = preprocess_image(image_bytes)
    engine = _get_structure_engine()
    return _run_structure(engine, arr, page=0)


def extract_from_pdf_pages(page_images: list[bytes]) -> ExtractionResult:
    """Run PP-StructureV2 across multiple rendered PDF pages and merge results."""
    engine = _get_structure_engine()

    merged_headers: list[str] | None = None
    merged_rows: list[dict[str, str]] = []
    merged_header_bboxes: dict[str, BoundingBox] = {}
    merged_cell_bboxes: dict[tuple[int, str], BoundingBox] = {}
    merged_confidences: dict[tuple[int, str], float] = {}
    row_offset = 0

    for page_idx, image_bytes in enumerate(page_images):
        arr, _ = preprocess_image(image_bytes)
        page_result = _run_structure(engine, arr, page=page_idx)

        if not page_result.headers:
            continue

        if merged_headers is None:
            merged_headers = page_result.headers
            merged_header_bboxes = page_result.header_bboxes
        elif page_result.headers != merged_headers:
            # Different column structure on subsequent page — skip (likely footer/header)
            continue

        for local_idx, row in enumerate(page_result.rows):
            global_idx = row_offset + local_idx
            merged_rows.append(row)
            for header in merged_headers:
                local_key = (local_idx, header)
                global_key = (global_idx, header)
                if local_key in page_result.cell_bboxes:
                    merged_cell_bboxes[global_key] = page_result.cell_bboxes[local_key]
                if local_key in page_result.cell_confidences:
                    merged_confidences[global_key] = page_result.cell_confidences[local_key]

        row_offset += len(page_result.rows)

    headers = merged_headers or []
    return ExtractionResult(
        headers=headers,
        rows=merged_rows,
        preview=merged_rows[:5],
        total_rows=len(merged_rows),
        header_bboxes=merged_header_bboxes,
        cell_bboxes=merged_cell_bboxes,
        cell_confidences=merged_confidences,
    )


def _run_structure(engine, img_array: np.ndarray, page: int) -> ExtractionResult:
    """Run PP-StructureV2 on one image array and extract the dominant table."""
    result = engine(img_array)

    # Find the table region with the most cells
    table_region = None
    for region in result:
        if region.get("type") == "table":
            if table_region is None or (
                len(region.get("res", {}).get("html", ""))
                > len(table_region.get("res", {}).get("html", ""))
            ):
                table_region = region

    if table_region is None:
        return ExtractionResult(headers=[], rows=[], preview=[], total_rows=0)

    return _parse_table_region(table_region, page)


def _parse_table_region(region: dict, page: int) -> ExtractionResult:
    """Extract headers, rows, bounding boxes, and confidence scores from a PP-StructureV2 table region."""
    res = region.get("res", {})

    # PP-StructureV2 provides cell-level recognition results
    cell_results: list[dict] = res.get("cell_bbox", [])
    rec_res: list[list] = res.get("rec_res", [[]])  # [[text, confidence], ...]

    if not cell_results and not rec_res:
        return ExtractionResult(headers=[], rows=[], preview=[], total_rows=0)

    # Attempt structured extraction from HTML output
    try:
        from html.parser import HTMLParser
        cells = _parse_html_table(res.get("html", ""))
    except Exception:
        cells = []

    if not cells:
        return ExtractionResult(headers=[], rows=[], preview=[], total_rows=0)

    # First row is assumed to be headers
    headers = [str(c).strip() for c in cells[0]]
    headers = [h if h else f"col_{i + 1}" for i, h in enumerate(headers)]

    header_bboxes: dict[str, BoundingBox] = {}
    cell_bboxes: dict[tuple[int, str], BoundingBox] = {}
    cell_confidences: dict[tuple[int, str], float] = {}

    # Match bounding boxes from cell_bbox list if available
    bbox_list = _extract_bbox_list(cell_results)
    conf_list = [item[1] if len(item) > 1 else 1.0 for item in rec_res]

    data_rows: list[dict[str, str]] = []
    flat_cell_idx = 0

    for row_idx, row in enumerate(cells[1:]):
        padded = row + [""] * (len(headers) - len(row))
        row_dict: dict[str, str] = {}
        for col_idx, (header, value) in enumerate(zip(headers, padded)):
            row_dict[header] = str(value).strip()

            if flat_cell_idx < len(bbox_list):
                b = bbox_list[flat_cell_idx]
                box = BoundingBox(x=b[0], y=b[1], w=b[2] - b[0], h=b[3] - b[1], page=page)
                cell_bboxes[(row_idx, header)] = box
            if flat_cell_idx < len(conf_list):
                cell_confidences[(row_idx, header)] = float(conf_list[flat_cell_idx])

            flat_cell_idx += 1

        data_rows.append(row_dict)

    return ExtractionResult(
        headers=headers,
        rows=data_rows,
        preview=data_rows[:5],
        total_rows=len(data_rows),
        header_bboxes=header_bboxes,
        cell_bboxes=cell_bboxes,
        cell_confidences=cell_confidences,
    )


def _parse_html_table(html: str) -> list[list[str]]:
    """Parse HTML table string into a 2D list of cell strings."""
    from html.parser import HTMLParser

    class TableParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.rows: list[list[str]] = []
            self._current_row: list[str] = []
            self._in_cell = False
            self._cell_text = ""

        def handle_starttag(self, tag, attrs):
            if tag in ("td", "th"):
                self._in_cell = True
                self._cell_text = ""
            elif tag == "tr":
                self._current_row = []

        def handle_endtag(self, tag):
            if tag in ("td", "th"):
                self._current_row.append(self._cell_text.strip())
                self._in_cell = False
            elif tag == "tr":
                if self._current_row:
                    self.rows.append(self._current_row)

        def handle_data(self, data):
            if self._in_cell:
                self._cell_text += data

    parser = TableParser()
    parser.feed(html)
    return parser.rows


def _extract_bbox_list(cell_results: list) -> list[list[float]]:
    """Flatten bounding box data from PP-StructureV2 cell_bbox format."""
    bboxes = []
    for item in cell_results:
        if isinstance(item, (list, tuple)) and len(item) >= 4:
            bboxes.append([float(v) for v in item[:4]])
    return bboxes
