"""Excel extractor — openpyxl.

Handles .xlsx, .xls (via fallback), .ods.
Key behaviors:
- Scans all sheets and returns names + row counts for user selection
- Auto-detects header row: first row in the first 10 where majority of cells are non-numeric strings
- Unmerges all merged cells and propagates the merged cell value to all constituent cells
- Converts every cell value to a stripped string
"""

from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from backend.services.ingestion_service.extractors.base import ExtractionResult


def extract(file_path: str | Path, sheet_name: str | None = None) -> ExtractionResult:
    wb = openpyxl.load_workbook(str(file_path), data_only=True)

    available_sheets = [
        {"name": sheet, "row_count": wb[sheet].max_row}
        for sheet in wb.sheetnames
    ]

    target_sheet = sheet_name or wb.sheetnames[0]
    ws = wb[target_sheet]

    _unmerge_and_propagate(ws)

    header_row_idx = _detect_header_row(ws)
    headers = _read_row_as_strings(ws, header_row_idx)
    headers = [h if h else f"colonne_{i + 1}" for i, h in enumerate(headers)]

    data_rows: list[dict[str, str]] = []
    for row_idx in range(header_row_idx + 1, ws.max_row + 1):
        row_values = _read_row_as_strings(ws, row_idx)
        if all(v == "" for v in row_values):
            continue
        data_rows.append(dict(zip(headers, row_values)))

    return ExtractionResult(
        headers=headers,
        rows=data_rows,
        preview=data_rows[:5],
        total_rows=len(data_rows),
        available_sheets=available_sheets,
        selected_sheet=target_sheet,
    )


def _unmerge_and_propagate(ws: Worksheet) -> None:
    """Unmerge all merged cell ranges and fill every constituent cell with the top-left value."""
    # Collect ranges first to avoid mutation during iteration
    merged_ranges = list(ws.merged_cells.ranges)
    for merge_range in merged_ranges:
        top_left_value = ws.cell(merge_range.min_row, merge_range.min_col).value
        ws.unmerge_cells(str(merge_range))
        for row in range(merge_range.min_row, merge_range.max_row + 1):
            for col in range(merge_range.min_col, merge_range.max_col + 1):
                ws.cell(row, col).value = top_left_value


def _detect_header_row(ws: Worksheet) -> int:
    """Return 1-based row index of the most likely header row within the first 10 rows."""
    best_row = 1
    best_score = -1

    for row_idx in range(1, min(11, ws.max_row + 1)):
        values = _read_row_as_strings(ws, row_idx)
        non_empty = [v for v in values if v]
        if not non_empty:
            continue

        non_numeric = sum(1 for v in non_empty if not _is_numeric(v))
        score = non_numeric / len(non_empty)

        if score > best_score:
            best_score = score
            best_row = row_idx

    return best_row


def _read_row_as_strings(ws: Worksheet, row_idx: int) -> list[str]:
    values = []
    for col_idx in range(1, ws.max_column + 1):
        cell = ws.cell(row_idx, col_idx)
        val = cell.value
        values.append(str(val).strip() if val is not None else "")
    return values


def _is_numeric(value: str) -> bool:
    try:
        float(value.replace(",", ".").replace(" ", ""))
        return True
    except ValueError:
        return False
