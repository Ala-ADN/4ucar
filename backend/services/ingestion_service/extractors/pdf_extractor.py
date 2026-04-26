"""PDF extractor — PyMuPDF.

Native PDF (selectable text): extracts text per page, reconstructs tabular
structure from consistent spacing/alignment.

Scanned PDF detection: if page 1 yields < 50 characters of text, caller
should use ocr_extractor instead. This module only handles native PDFs.
"""

from pathlib import Path

import fitz  # PyMuPDF

from backend.services.ingestion_service.extractors.base import ExtractionResult

_NATIVE_TEXT_THRESHOLD = 50  # characters on first page to classify as native


def is_native_pdf(file_path: str | Path) -> bool:
    """Return True if the PDF has selectable text (not a pure scan)."""
    doc = fitz.open(str(file_path))
    try:
        text = doc[0].get_text()
        return len(text.strip()) >= _NATIVE_TEXT_THRESHOLD
    finally:
        doc.close()


def extract(file_path: str | Path) -> ExtractionResult:
    """Extract tabular data from a native (text-layer) PDF."""
    doc = fitz.open(str(file_path))
    all_rows: list[list[str]] = []

    try:
        for page in doc:
            page_rows = _extract_page_table(page)
            all_rows.extend(page_rows)
    finally:
        doc.close()

    if not all_rows:
        return ExtractionResult(headers=[], rows=[], preview=[], total_rows=0)

    # Heuristic: the row with the most non-numeric strings is the header
    header_idx = _find_header_row(all_rows)
    headers = all_rows[header_idx]
    headers = [h if h else f"colonne_{i + 1}" for i, h in enumerate(headers)]

    data_rows: list[dict[str, str]] = []
    for row in all_rows[header_idx + 1:]:
        if all(cell == "" for cell in row):
            continue
        padded = row + [""] * (len(headers) - len(row))
        data_rows.append(dict(zip(headers, padded[:len(headers)])))

    return ExtractionResult(
        headers=headers,
        rows=data_rows,
        preview=data_rows[:5],
        total_rows=len(data_rows),
    )


def render_pages_as_images(file_path: str | Path, dpi: int = 300) -> list[bytes]:
    """Render each PDF page as a PNG bytes object for the OCR pipeline."""
    doc = fitz.open(str(file_path))
    images = []
    try:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            images.append(pix.tobytes("png"))
    finally:
        doc.close()
    return images


def _extract_page_table(page: fitz.Page) -> list[list[str]]:
    """Extract table rows from a page using PyMuPDF's built-in table finder."""
    # PyMuPDF 1.23+ has a find_tables() method
    try:
        tabs = page.find_tables()
        if tabs.tables:
            # Use the largest table on the page
            largest = max(tabs.tables, key=lambda t: t.row_count * t.col_count)
            extracted = largest.extract()
            return [
                [str(cell).strip() if cell is not None else "" for cell in row]
                for row in extracted
            ]
    except AttributeError:
        pass

    # Fallback: text-based reconstruction using word positions
    return _reconstruct_from_words(page)


def _reconstruct_from_words(page: fitz.Page) -> list[list[str]]:
    """Group words into rows by their y-coordinate proximity."""
    words = page.get_text("words")  # (x0, y0, x1, y1, word, block, line, word_num)
    if not words:
        return []

    # Cluster words by y-band
    y_tolerance = 5
    rows: dict[float, list[tuple[float, str]]] = {}
    for word in words:
        x0, y0, x1, y1, text = word[:5]
        # Round y to nearest band
        band = round(y0 / y_tolerance) * y_tolerance
        rows.setdefault(band, []).append((x0, str(text)))

    result = []
    for y_key in sorted(rows):
        row_words = sorted(rows[y_key], key=lambda w: w[0])
        result.append([w[1] for w in row_words])

    return result


def _find_header_row(rows: list[list[str]]) -> int:
    best_idx = 0
    best_score = -1
    for i, row in enumerate(rows[:10]):
        non_empty = [c for c in row if c]
        if not non_empty:
            continue
        non_numeric = sum(1 for c in non_empty if not _is_numeric(c))
        score = non_numeric / len(non_empty)
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx


def _is_numeric(value: str) -> bool:
    try:
        float(value.replace(",", ".").replace(" ", "").replace("\xa0", ""))
        return True
    except ValueError:
        return False
