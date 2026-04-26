# Data Ingestion Service — Implementation Reference

> Status: Active implementation · April 2026
> Service path: `backend/services/ingestion_service/`

---

## Purpose

Standalone FastAPI microservice that is the single entry point for all structured data into the UCAR KPI database. Converts Excel/CSV/PDF/image uploads into validated, committed data records. Publishes `data.committed` events to Redis pub/sub after successful commit so the analytics layer can recompute KPIs.

---

## Runtime Components

| Component | Command | Responsibility |
|---|---|---|
| FastAPI app | `uvicorn ingestion_service.main:app` | HTTP: receive, status, confirm, commit |
| Extraction workers | `celery -A workers.celery_app worker -Q extraction` | Parse files |
| OCR workers | `celery -A workers.celery_app worker -Q ocr -c 2` | PaddleOCR — CPU/GPU bound |
| Mapping workers | `celery -A workers.celery_app worker -Q mapping` | Claude API call |

---

## Pipeline Stages

```
Upload → extracted → mapping_proposed → mapping_confirmed → validated → committed
                                                          ↘ (quarantine review if needed)
```

Each transition is **user-triggered** — nothing advances automatically without confirmation.

| Stage | Status Before | Status After | Trigger |
|---|---|---|---|
| 1. Receive & enqueue | — | `pending` | POST /upload |
| 2. Extraction | `pending` | `extracted` | Celery auto |
| 3. AI mapping | `extracted` | `mapping_proposed` | GET /mapping (enqueues) |
| 4. User confirms | `mapping_proposed` | `mapping_confirmed` | POST /mapping |
| 5. Normalize + validate | `mapping_confirmed` | `validated` | Celery auto |
| 6. Quarantine review | `validated` | — | User-driven, optional |
| 7. Commit | `validated` | `committed` | POST /commit |

---

## File Layout

```
backend/services/ingestion_service/
├── main.py                      # FastAPI app factory
├── config.py                    # IngestionSettings (pydantic-settings)
├── kpi_schema.py                # KPI_FIELDS master dict + alias helper
├── models/
│   ├── import_record.py         # ImportRecord, DataRecord, QuarantineRow, DataRequest
│   └── audit.py                 # AuditEntry (append-only)
├── extractors/
│   ├── base.py                  # ExtractionResult dataclass
│   ├── excel.py                 # openpyxl — sheet scan, header detect, unmerge
│   ├── csv_extractor.py         # chardet + delimiter auto-detect
│   ├── pdf_extractor.py         # PyMuPDF native text extraction
│   └── ocr_extractor.py         # PaddleOCR PP-StructureV2 + bounding boxes
├── mapping/
│   ├── claude_mapper.py         # Claude API call + validation
│   └── fuzzy_mapper.py          # difflib fallback
├── normalizer.py                # Value transformations (FR numbers, Arabic digits, etc.)
├── validator.py                 # Business rule validation → valid/warned/invalid
├── routers/
│   ├── upload.py                # POST /upload
│   ├── imports.py               # GET|POST /imports/{id}/...
│   ├── quarantine.py            # GET|POST quarantine routes
│   ├── audit.py                 # GET /audit
│   ├── requests.py              # Data request management
│   └── health.py                # GET /health
├── dependencies.py              # get_current_user, require_role, get_db
└── tasks.py                     # Celery task definitions (extraction, mapping, validation)
```

---

## Key Design Decisions

### PaddleOCR over Tesseract
The build prompt specifies PaddleOCR with PP-StructureV2 (not basic OCR). This gives structured table output with per-cell bounding boxes — essential for the visual grounding feature where the frontend highlights source regions when a user hovers over extracted values.

### Claude mapping is prototype only
The Claude API is called with column headers only — no row data ever leaves the server. Production replacement is `intfloat/multilingual-e5-large` running locally. The interface is identical so swapping is a one-file change. See `mapping/claude_mapper.py` comment.

### Quarantine is hard
Invalid rows go to `quarantine_rows` table. They are never imported automatically. An `ucar_analyst` or `super_admin` can force-override with audit log. Institution-level roles cannot.

### Commit conflict modes
- `overwrite`: archive existing records (soft delete), write new ones
- `merge`: only update fields present in new import
- `cancel`: abort — returns 409, no changes

### File storage
`uploads/{import_id}/{original_filename}` on local disk. Files retained ≥ 12 months. MinIO migration path: change `UPLOAD_DIR` to a MinIO-backed path adapter — no code change to callers.

---

## Validation Rules Quick Reference

See `validator.py` for full implementation. Summary:

- **Universal**: percentage 0–100, counts ≥ 0, required non-null, type-correct after normalization
- **Academic**: success+dropout+repetition ≤ 100; success=100 or <20 → warn; STR >80 → warn
- **Financial**: consumed > allocated+20% → invalid; cross-check declared vs computed rate
- **Operational**: teaching_staff=0 → invalid; admin > 3× teaching → warn
- **Environmental**: energy=0 → warn; month-over-month >200% → warn
- **Cross-period**: compare against previous period for same institution+field, warn on large deltas

---

## Auth Roles (ingestion-specific mapping)

The ingestion service uses a simplified 4-role model that maps to the platform RBAC:

| Ingestion role | Platform role | Key capabilities |
|---|---|---|
| `super_admin` | `super_admin` | Unlock periods, force rollback, purge files |
| `ucar_analyst` | `ucar_analyst` | Cross-institution, historical import, force quarantine override |
| `institution_director` | `institution_director` | Own institution only, can view but not override |
| `institution_admin` | `institution_admin` | Own institution only, primary uploaders |

---

## Redis Events

After successful commit, publishes to channel `data.events`:

```json
{
  "event": "data.committed",
  "institution_id": "uuid",
  "period": "2025-S1",
  "domain": "academic",
  "import_id": "uuid",
  "record_count": 42,
  "committed_at": "2026-04-25T10:00:00Z"
}
```

---

## Environment Variables (ingestion-specific additions to .env)

```
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
MAX_PDF_PAGES=30
OCR_CONFIDENCE_HIGH=0.90
OCR_CONFIDENCE_LOW=0.60
CLAUDE_TIMEOUT_SECONDS=15
CLAUDE_MAX_RETRIES=2
ROLLBACK_WINDOW_DAYS=7
FILE_RETENTION_DAYS=365
```
