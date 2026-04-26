"""Base types shared by all extractor modules."""

from dataclasses import dataclass, field


@dataclass
class BoundingBox:
    """Pixel coordinates of an OCR-detected cell, relative to its page image."""
    x: float
    y: float
    w: float
    h: float
    page: int = 0


@dataclass
class ExtractionResult:
    """Uniform output produced by every extractor."""
    headers: list[str]
    rows: list[dict[str, str]]  # {header: raw_string_value}
    preview: list[dict[str, str]]  # first 5 rows
    total_rows: int

    # OCR-specific — populated only for scanned sources
    # Maps header → BoundingBox for the header row cell
    header_bboxes: dict[str, BoundingBox] = field(default_factory=dict)
    # Maps (row_index, header) → BoundingBox
    cell_bboxes: dict[tuple[int, str], BoundingBox] = field(default_factory=dict)
    # Maps (row_index, header) → confidence float 0–1
    cell_confidences: dict[tuple[int, str], float] = field(default_factory=dict)

    # Multi-sheet metadata
    available_sheets: list[dict] = field(default_factory=list)  # [{name, row_count}]
    selected_sheet: str | None = None

    # For CSV: surfaces ambiguous delimiter/encoding candidates to the user
    encoding_candidates: list[str] = field(default_factory=list)
    delimiter_candidates: list[str] = field(default_factory=list)
