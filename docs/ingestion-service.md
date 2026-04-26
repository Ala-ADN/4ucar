# Ingestion Service

**Path:** [backend/services/ingestion_service/](../backend/services/ingestion_service/)
**Port:** 8010
**Purpose:** the only entry point for institutional data into the KPI database.

## Why this service exists

Every Tunisian university ERP project we benchmarked failed at the same place: each institution has a slightly different Excel template, and converting "their format" into "our schema" is hard, tedious, and unforgiving. The ingestion service is the answer to that. It handles five formats (xlsx, ods, csv, native PDF, scanned PDF/image), proposes a column-to-KPI-field mapping, lets the user correct it, validates each value, then commits — and remembers the mapping as a *template* so the next upload of the same shape skips human review entirely.

## End-to-end pipeline

```
upload  →  extraction  →  template match  →  mapping  →  validation  →  commit
                                  ▲                                       │
                                  └────── auto-confirm if score ≥ 0.6 ────┘
```

Each arrow is a state transition on `ImportRecord.status`. Each step except the first runs in a Celery worker and writes its result back to the `ImportRecord` row.

### 1. Upload — [routers/upload.py](../backend/services/ingestion_service/routers/upload.py)

- Streams the file to disk in 1 MB chunks; rejects on size overrun mid-stream so we never write a 500 MB file just to discard it.
- Detects MIME by **magic bytes** (PK header, %PDF, JPEG/PNG/TIFF signatures), not by the client-provided `Content-Type` (which is unreliable from browsers).
- Creates an `ImportRecord` with `status="pending"`, writes a French audit entry, enqueues `run_extraction` on the `extraction` queue, returns `202 Accepted` with the `import_id`.

### 2. Extraction — [extractors/](../backend/services/ingestion_service/extractors/)

Five extractors share one base type, [`ExtractionResult`](../backend/services/ingestion_service/extractors/base.py):

```python
@dataclass
class ExtractionResult:
    headers: list[str]
    rows: list[dict[str, str]]
    preview: list[dict[str, str]]      # first 5 rows for the UI
    total_rows: int
    # OCR-only:
    header_bboxes: dict[str, BoundingBox]
    cell_bboxes: dict[tuple[int, str], BoundingBox]
    cell_confidences: dict[tuple[int, str], float]
    # Excel-only:
    available_sheets: list[dict]
    selected_sheet: str | None
    # CSV-only:
    encoding_candidates: list[str]
    delimiter_candidates: list[str]
```

This uniform shape is the contract the rest of the pipeline expects. **The mapping and validation stages don't know if the data came from a spreadsheet or a phone photo.**

| Extractor | File | Library | Notes |
|---|---|---|---|
| Excel | `excel.py` | `openpyxl` | Multi-sheet aware; sheet picker shown if >1 |
| CSV | `csv_extractor.py` | `pandas` + `chardet` | Detects encoding (utf-8 vs windows-1252 vs latin-1) and delimiter (`,`, `;`, `\t`) |
| Native PDF | `pdf_extractor.py` | `PyMuPDF` (fitz) | Reads embedded text first; if a page has no text, renders to image and falls through to OCR |
| Scanned PDF | `pdf_extractor.py` → `ocr_extractor.py` | `PyMuPDF` for rasterization, `paddleocr` for OCR | One image per page, hard cap at `MAX_PDF_PAGES=30` |
| Image | `ocr_extractor.py` | `paddleocr` PP-StructureV2 | Direct JPG/PNG/TIFF/WEBP |

#### OCR specifics

PaddleOCR PP-StructureV2 returns *structured* output: per-cell bbox + recognition confidence. We use this to produce a tiered UX in the frontend:

- ≥ 0.90 confidence → green, pre-populated, no acknowledgement needed
- 0.60–0.90 → yellow, pre-populated, user must confirm
- < 0.60 → field left empty; raw OCR text + the cell's image region shown side-by-side
- not detected → required-field validation flags it

The bounding box is also stored in `data_records.bounding_box` so an auditor can later click a value and see the source pixel region.

CPU-only build, pinned to `paddlepaddle==2.6.2`, `paddleocr<3.0.0`, `albumentations==1.3.1` — those exact versions because newer paddleocr drags in `torch` via `albumentations>=2.x` and the install becomes 2 GB.

### 3. Template match — [templates_matcher.py](../backend/services/ingestion_service/templates_matcher.py)

Before calling any LLM, we check whether this institution has uploaded a file with the same headers before.

- Lowercase + de-accent + tokenise headers.
- Score against every saved `DocumentTemplate` for this institution + domain using **Jaccard overlap** on token bags.
- Domain match and format match are multiplicative gates: they zero the score when they disagree.
- Score ≥ 0.60 → auto-confirm: the saved mapping is applied and the pipeline jumps straight to validation.
- 0.35 ≤ score < 0.60 → suggested template shown, user can accept or override.
- < 0.35 → no suggestion; fall through to LLM mapping.

This is **not** embedding similarity. We tried it; we don't need it. KPI field labels and Tunisian ministerial form headers reuse the same nouns ("inscrits", "diplômés", "chercheurs"), and Jaccard scores them well in practice. The matcher exposes a stable `score()` interface, so swapping in a sentence-transformer model later changes nothing else.

### 4. Mapping — [mapping/](../backend/services/ingestion_service/mapping/)

Three mappers, in priority order:

| File | Strategy | When it runs |
|---|---|---|
| `gemini_mapper.py` | Calls Google Gemini with the headers + the domain's KPI field catalog as context, returns a JSON proposal | Default in this build |
| `claude_mapper.py` | Same, but using Anthropic Claude | Available, swappable |
| `fuzzy_mapper.py` | `difflib.get_close_matches` against an alias map built from `kpi_schema.py` | Fallback when the LLM call fails or returns unparseable JSON |

The fallback is what enforces *data sovereignty*: the system always ingests, even when the network is down or API keys are missing. The proposal is written to `import_record.mapping_proposal` and presented to the user. The user's confirmation is stored in `confirmed_mapping`.

### 5. Validation + normalization — [validator.py](../backend/services/ingestion_service/validator.py), [normalizer.py](../backend/services/ingestion_service/normalizer.py)

For each row:

- **Normalize** strings to typed values (numbers with `,` or `.` decimals, dates `JJ/MM/AAAA` or ISO, booleans `oui/non`, percentages `60%` → 0.60).
- **Validate** against the field's typed contract (range, regex, enum). Failed rows go to `quarantine_rows` with `failure_reason_fr`. Soft warnings stay on the record (`is_warned=True`).

Quarantined rows are **not** committed. The user can review them in the UI, correct, override (with justification, if they hold `Permission.OVERRIDE_QUARANTINE`), or discard.

### 6. Commit

A single transaction:

1. Inserts `data_records` rows for every passing row.
2. Soft-archives prior overlapping records (same institution + period + field) if the user chose `overwrite`. `is_archived=True`, `archived_by_import_id` set.
3. Updates `import_record.status="committed"`, fills the `records_*` counters.
4. Publishes a `data.committed` message on Redis channel `data.events` so the KPI service can recompute.

Inside `ROLLBACK_WINDOW_DAYS=7` (env-configurable) the entire commit can be reverted by un-archiving prior rows and archiving the new ones — symmetric.

## Routers

| Router | Purpose |
|---|---|
| `health.py` | `GET /healthz` |
| `upload.py` | `POST /upload` |
| `imports.py` | `GET /imports/{id}`, `GET /imports/{id}/status`, `POST /imports/{id}/confirm-mapping`, `POST /imports/{id}/commit`, `POST /imports/{id}/rollback` |
| `quarantine.py` | List + resolve quarantined rows |
| `templates.py` | CRUD on saved `DocumentTemplate`s |
| `audit.py` | Read audit log (gated by `VIEW_AUDIT_LOG`) |
| `requests.py` | UCAR-central data-collection requests sent to institutions |

## What you'll be asked

- *"How does the system handle a scanned form?"* — it goes through `ocr_extractor.py`, each cell carries a confidence and a bbox, the UI surfaces low-confidence cells for human review, and after commit those bboxes are queryable from `data_records.bounding_box`.
- *"What if the LLM mapper hallucinates?"* — the proposal is *never* applied without user confirmation (unless an existing template auto-confirms by Jaccard score, which is purely local). The LLM is a UX assistant, not a source of truth.
- *"What stops two analysts from racing on the same import?"* — `ImportRecord.status` transitions are sequential; a confirm or commit on a record not in the expected status returns `409 Conflict`.
- *"Why French error messages?"* — required by the Tunisian Ministry's UX standards for institutional users; `failure_reason_fr` on quarantined rows is what shows up in the report exported to MESRS.
