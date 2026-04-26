# UCAR Demo Runbook

## What's actually built

| Layer | Component | Status |
|---|---|---|
| Backend | `ingestion_service` (port 8010) | ✅ Working — upload, extract (xlsx/csv/pdf/img), OCR, mapping, validation, commit, templates |
| Backend | `kpi_service` (port 8002) | ✅ KPI catalog, accreditation, professors, recompute |
| Frontend | React app (port 3000) | ✅ Wired to both backends via Vite proxy |
| Workers | Celery (extraction, mapping, ocr queues) | ✅ Working |
| Storage | PostgreSQL on `172.31.160.1:5432`, Redis on `localhost:6379` | ✅ Running |

Removed: 8 empty placeholder services (admin/auth/hr/nlp/project/report/alert/gateway). The frontend never called them.

## Start everything (3 terminals in WSL)

**Terminal 1 — Celery worker (handles extraction + OCR + mapping):**
```bash
cd /mnt/c/HACK4UCAR/4ucar
uv run celery -A backend.workers.celery_app worker -Q extraction,mapping,ocr -l INFO
```

**Terminal 2 — Ingestion service:**
```bash
cd /mnt/c/HACK4UCAR/4ucar
uv run uvicorn backend.services.ingestion_service.main:app --port 8010
```

**Terminal 3 — KPI service:**
```bash
cd /mnt/c/HACK4UCAR/4ucar
uv run uvicorn backend.services.kpi_service.main:app --port 8002
```

**Terminal 4 (PowerShell) — Frontend:**
```powershell
cd C:\HACK4UCAR\4ucar\FrontEnd
npm run dev
```

Open: **http://localhost:3000**

## Demo flow (5 min)

1. **Open the app** → http://localhost:3000
2. **Navigate to "Téléversement de données"** (Ingestion page)
3. **Upload an Excel file** with KPI columns:
   - Drop your `student_grades.xlsx` (or any tabular file)
   - Pick domain (e.g. Académique), period (e.g. 2026-S1)
   - Click "Téléverser"
4. **The page auto-polls** the backend:
   - Status badge: `pending` → `extracted`
   - Detected columns appear as chips
   - Template matcher runs automatically
5. **Save the mapping as a template** — fill name, click "Sauvegarder le mapping"
6. **Click "Engager les données"** to commit

Re-upload another file with the same columns: the template is auto-applied (auto_confirm badge).

## What to talk about with the jury

- **Data ingestion is the hard part** — most KPI projects fail because every institution has a slightly different Excel template. We solved it with:
  - Multi-format extractors (xlsx/csv/native PDF/scanned PDF via OCR/images)
  - PaddleOCR PP-StructureV2 for scanned documents (per-cell bbox + confidence)
  - Identity column mapping with template memorization (no AI required after first upload)
- **Pipeline is async** — Celery workers separate fast extraction from slow OCR
- **Data sovereignty** — no external API calls in the prototype's hot path; OCR runs locally, mapping uses string matching
- **Accreditation engine** is in `kpi_service/domain/accreditation.py` with framework definitions, control tests, and gap analysis (Domain H, separate from numeric KPIs)

## If something breaks during the demo

- 500 on upload → check Postgres connection (`172.31.160.1:5432`) and `.env` `DATABASE_URL`
- Stuck on `pending` status → check Celery worker is running with all 3 queues
- Frontend shows network error → backend isn't running or proxy port mismatch
- Token expired → app uses dev fallback when `APP_ENV=local` (see `dependencies.py`)
