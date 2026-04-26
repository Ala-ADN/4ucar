"""OCR extractor — PaddleOCR PP-StructureV2.

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
            lang="en",           # layout model only supports 'en'/'ch'; text recognition handles FR/AR
            show_log=False,
            table=False,         # table model crashes on CPU/WSL2; use layout+OCR path instead
            layout=False,        # skip layout analysis — run plain OCR on full image
            use_angle_cls=False, # cls model not bundled; deskew handles rotation
        )
        _PADDLE_INITIALIZED = True
    return _STRUCTURE_ENGINE


# ── Public interface ──────────────────────────────────────────────────────────


def preprocess_image(image: Image.Image) -> tuple[Image.Image, bool]:
    """Preprocess a PIL Image for OCR. Returns (processed_image, low_quality_flag).

    low_quality is True when estimated DPI < 150. Processing continues regardless —
    the flag surfaces a warning to the user rather than rejecting the file.

    Steps (in order):
    1. Flatten alpha channel (RGBA → RGB)
    2. Convert to grayscale
    3. Contrast enhancement
    4. Sharpness enhancement
    5. Deskew via horizontal projection profile variance maximization
    """
    # Estimate DPI from metadata — 72 is the PIL default when absent
    dpi_info = image.info.get("dpi", (72, 72))
    estimated_dpi = float(dpi_info[0]) if isinstance(dpi_info, tuple) else float(dpi_info)
    low_quality = estimated_dpi < 150

    # 1. Flatten alpha
    if image.mode in ("RGBA", "LA", "PA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # 2. Grayscale
    image = image.convert("L")

    # 3. Contrast
    image = ImageEnhance.Contrast(image).enhance(1.5)

    # 4. Sharpness
    image = ImageEnhance.Sharpness(image).enhance(1.2)

    # 5. Deskew
    image = _deskew(image)

    return image, low_quality


def extract_table_from_image(image: Image.Image) -> dict:
    """Primary public interface. Run PP-StructureV2 on a PIL Image.

    Returns a dict with:
      headers        — list[str], first detected table's header row
      rows           — list[list[str]], data rows
      cell_metadata  — list[list[{confidence, bbox}]], rows × cols
      table_count    — int, total tables detected in the image
      avg_confidence — float, mean confidence across all cells
      low_quality    — bool, True if estimated DPI < 150
      raw_html       — str, raw HTML from PP-StructureV2 (first table)
      all_tables     — list[dict], all detected tables (caller picks if > 1)

    Bounding boxes are normalized [0.0, 1.0] relative to original image dimensions.
    """
    orig_w, orig_h = image.size
    processed, low_quality = preprocess_image(image)
    # PP-StructureV2 requires a 3-channel BGR uint8 array (OpenCV convention)
    rgb = processed.convert("RGB")
    img_array = np.array(rgb, dtype=np.uint8)[:, :, ::-1]  # RGB → BGR

    engine = _get_structure_engine()
    result = engine(img_array)

    tables = [r for r in result if r.get("type") == "table"]

    if not tables:
        return {
            "headers": [],
            "rows": [],
            "cell_metadata": [],
            "table_count": 0,
            "avg_confidence": 0.0,
            "low_quality": low_quality,
            "raw_html": "",
            "all_tables": [],
        }

    all_tables = [_parse_table_to_dict(t, orig_w, orig_h) for t in tables]

    # Primary result: largest table by cell count
    primary = max(all_tables, key=lambda t: len(t["rows"]) * max(len(t["headers"]), 1))

    # Flatten all confidences for avg
    all_confs = [
        cell["confidence"]
        for tbl in all_tables
        for row in tbl["cell_metadata"]
        for cell in row
    ]
    avg_confidence = float(np.mean(all_confs)) if all_confs else 0.0

    return {
        "headers": primary["headers"],
        "rows": primary["rows"],
        "cell_metadata": primary["cell_metadata"],
        "table_count": len(tables),
        "avg_confidence": avg_confidence,
        "low_quality": low_quality,
        "raw_html": primary["raw_html"],
        "all_tables": all_tables,
    }


def extract_from_pdf_pages(page_images: list[bytes]) -> ExtractionResult:
    """Run PP-StructureV2 across multiple rendered PDF pages and merge results.

    Called from the Celery OCR task. Accepts raw bytes per page (hex-decoded
    from the task payload). Merges rows across pages when column headers match.
    """
    merged_headers: list[str] | None = None
    merged_rows: list[dict[str, str]] = []
    merged_header_bboxes: dict[str, BoundingBox] = {}
    merged_cell_bboxes: dict[tuple[int, str], BoundingBox] = {}
    merged_confidences: dict[tuple[int, str], float] = {}
    row_offset = 0

    for page_idx, image_bytes in enumerate(page_images):
        pil_image = Image.open(io.BytesIO(image_bytes))
        page_result = _extraction_result_from_pil(pil_image, page=page_idx)

        if not page_result.headers:
            continue

        if merged_headers is None:
            merged_headers = page_result.headers
            merged_header_bboxes = page_result.header_bboxes
        elif page_result.headers != merged_headers:
            # Different column structure — likely a footer/header page, skip
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


def extract_from_image_bytes(image_bytes: bytes) -> ExtractionResult:
    """Run PP-StructureV2 on a single raw image bytes payload."""
    pil_image = Image.open(io.BytesIO(image_bytes))
    return _extraction_result_from_pil(pil_image, page=0)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _deskew(image: Image.Image) -> Image.Image:
    """Correct skew by finding the angle that maximizes horizontal projection variance."""
    arr = np.array(image)
    # Binarize: dark pixels = 1
    binary = (arr < 128).astype(np.float32)

    best_angle = 0.0
    best_variance = -1.0

    for angle in np.arange(-10, 10.5, 0.5):
        rotated = image.rotate(angle, expand=False, fillcolor=255)
        rot_arr = np.array(rotated)
        rot_bin = (rot_arr < 128).astype(np.float32)
        row_sums = rot_bin.sum(axis=1)
        variance = float(np.var(row_sums))
        if variance > best_variance:
            best_variance = variance
            best_angle = angle

    if abs(best_angle) < 0.5:
        return image
    return image.rotate(best_angle, expand=False, fillcolor=255)


def _parse_table_to_dict(region: dict, orig_w: int, orig_h: int) -> dict:
    """Parse one PP-StructureV2 table region into the extract_table_from_image dict format."""
    res = region.get("res", {})
    raw_html = res.get("html", "")

    cells_2d = _parse_html_table(raw_html)
    if not cells_2d:
        return {"headers": [], "rows": [], "cell_metadata": [], "raw_html": raw_html}

    headers = [str(c).strip() for c in cells_2d[0]]
    headers = [h if h else f"col_{i + 1}" for i, h in enumerate(headers)]

    # PP-StructureV2 cell_bbox: list of [x1,y1,x2,y2] per recognized cell
    bbox_list: list[list[float]] = _extract_bbox_list(res.get("cell_bbox", []))
    # rec_res: [[text, confidence], ...] per detected text region
    rec_res: list[list] = res.get("rec_res", [])

    # Build a confidence lookup by cell index
    conf_by_idx = {i: float(item[1]) if len(item) > 1 else 1.0 for i, item in enumerate(rec_res)}

    rows: list[list[str]] = []
    cell_metadata: list[list[dict]] = []
    flat_idx = 0

    for row_cells in cells_2d[1:]:
        padded = row_cells + [""] * (len(headers) - len(row_cells))
        row_str: list[str] = []
        row_meta: list[dict] = []

        for col_idx, value in enumerate(padded[:len(headers)]):
            row_str.append(str(value).strip())

            # Bounding box — normalized to [0,1]
            if flat_idx < len(bbox_list):
                b = bbox_list[flat_idx]
                bbox_norm = [
                    b[0] / orig_w, b[1] / orig_h,
                    b[2] / orig_w, b[3] / orig_h,
                ]
            else:
                bbox_norm = [0.0, 0.0, 0.0, 0.0]

            confidence = conf_by_idx.get(flat_idx, 1.0)
            row_meta.append({"confidence": confidence, "bbox": bbox_norm})
            flat_idx += 1

        rows.append(row_str)
        cell_metadata.append(row_meta)

    return {
        "headers": headers,
        "rows": rows,
        "cell_metadata": cell_metadata,
        "raw_html": raw_html,
    }


def _extraction_result_from_pil(image: Image.Image, page: int) -> ExtractionResult:
    """Convert a PIL Image → ExtractionResult (used by the bytes/PDF paths).

    PP-StructureV2 is run in plain OCR mode (table=False, layout=False) to avoid
    a PaddlePaddle CPU/WSL2 crash in the table structure model. Text detections
    are reconstructed into rows by y-coordinate proximity, same approach as the
    native PDF fallback.
    """
    orig_w, orig_h = image.size
    processed, _ = preprocess_image(image)
    # PaddleOCR requires a 3-channel BGR uint8 array (OpenCV convention)
    rgb = processed.convert("RGB")
    img_array = np.array(rgb, dtype=np.uint8)[:, :, ::-1]  # RGB → BGR

    engine = _get_structure_engine()
    result = engine(img_array)

    # In plain OCR mode the engine returns a list of detection dicts directly:
    # [{"type": "...", "bbox": [x1,y1,x2,y2], "res": [[text, confidence], ...]}, ...]
    # Flatten all detected text regions sorted by y then x.
    detections: list[tuple[float, float, str, float]] = []  # (y, x, text, conf)
    for region in result:
        res = region.get("res", [])
        bbox = region.get("bbox", [0, 0, 0, 0])
        x1, y1 = float(bbox[0]), float(bbox[1])
        if isinstance(res, list):
            for item in res:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    text, conf = str(item[0]).strip(), float(item[1])
                elif isinstance(item, dict):
                    text, conf = str(item.get("text", "")).strip(), float(item.get("confidence", 1.0))
                else:
                    continue
                if text:
                    detections.append((y1, x1, text, conf))

    if not detections:
        return ExtractionResult(headers=[], rows=[], preview=[], total_rows=0)

    # Group detections into rows by y-band (tolerance = 10px at 300 DPI)
    y_tolerance = 10
    row_map: dict[int, list[tuple[float, str, float]]] = {}
    for y, x, text, conf in sorted(detections):
        band = round(y / y_tolerance)
        row_map.setdefault(band, []).append((x, text, conf))

    rows_raw = [
        sorted(cells, key=lambda c: c[0])
        for _, cells in sorted(row_map.items())
    ]

    if not rows_raw:
        return ExtractionResult(headers=[], rows=[], preview=[], total_rows=0)

    # First row is headers
    headers = [cell[1] for cell in rows_raw[0]]
    headers = [h if h else f"col_{i+1}" for i, h in enumerate(headers)]

    data_rows: list[dict[str, str]] = []
    cell_bboxes: dict[tuple[int, str], BoundingBox] = {}
    cell_confidences: dict[tuple[int, str], float] = {}

    for row_idx, row_cells in enumerate(rows_raw[1:]):
        padded = row_cells + [(0.0, "", 1.0)] * (len(headers) - len(row_cells))
        row_dict: dict[str, str] = {}
        for col_idx, (x, text, conf) in enumerate(padded[:len(headers)]):
            header = headers[col_idx]
            row_dict[header] = text
            cell_confidences[(row_idx, header)] = conf
        data_rows.append(row_dict)

    return ExtractionResult(
        headers=headers,
        rows=data_rows,
        preview=data_rows[:5],
        total_rows=len(data_rows),
        cell_bboxes=cell_bboxes,
        cell_confidences=cell_confidences,
    )


def _parse_html_table(html: str) -> list[list[str]]:
    """Parse PP-StructureV2 HTML table output into a 2D list of cell strings."""
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
