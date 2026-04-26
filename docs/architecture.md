# Architecture

## One-sentence summary

A FastAPI monorepo where a **data-ingestion pipeline** turns institutional Excel/PDF/scan uploads into validated rows in PostgreSQL, a **KPI engine** computes domain-specific indicators on top of those rows, and a **React frontend** lets analysts and directors explore the result.

## Component map

```
┌──────────────────────┐
│   React + Vite SPA   │  port 3000
│      (FrontEnd)      │
└──────────┬───────────┘
           │  Vite dev proxy (/api → backend)
           ▼
┌──────────────────────┐     ┌──────────────────────┐    ┌──────────────────────┐
│  ingestion_service   │     │     kpi_service      │    │     rag_service      │
│       :8010          │     │        :8002         │    │  :8020 (scaffold)    │
│  upload / extract /  │     │  catalog, compute,   │    │  retrieve + generate │
│  map / validate /    │     │  accreditation,      │    │   over indexed data  │
│  commit              │     │  professors          │    │                      │
└────────┬─────────────┘     └──────────┬───────────┘    └──────────────────────┘
         │                              │
         │ writes ImportRecord +        │ reads data_records,
         │ DataRecord rows; publishes   │ writes kpi_records;
         │ "data.committed" on Redis    │ subscribes to data.events
         │                              │
         ▼                              ▼
┌──────────────────────────────────────────────────┐    ┌──────────────────────┐
│            PostgreSQL (TimescaleDB)              │    │        Redis         │
│  import_records │ data_records │ quarantine_rows │    │  pub/sub: data.events│
│  kpi_records    │ professors   │ frameworks      │    │  Celery broker (db1) │
│  document_templates │ audit_entries              │    │  Celery results (db2)│
└──────────────────────────────────────────────────┘    └──────────┬───────────┘
                                                                   │
                                                                   ▼
                                            ┌──────────────────────────────────┐
                                            │     Celery workers (3 queues)    │
                                            │  extraction │ mapping │ ocr      │
                                            └──────────────────────────────────┘
```

## Process boundaries

There are **three Python processes** at runtime:

| Process | Started by | Talks to |
|---|---|---|
| `ingestion_service` (uvicorn) | `uv run uvicorn backend.services.ingestion_service.main:app --port 8010` | Postgres, Redis (pubsub + Celery enqueue) |
| `kpi_service` (uvicorn) | `uv run uvicorn backend.services.kpi_service.main:app --port 8002` | Postgres, Redis (pubsub subscriber) |
| `celery worker` | `uv run celery -A backend.workers.celery_app worker -Q extraction,mapping,ocr -l INFO` | Postgres (sync engine), filesystem (uploads/), optional Anthropic/Gemini APIs |

The **frontend** is a fourth process (Vite dev server, port 3000) but runs only client code in the user's browser.

## Why three queues, not one?

OCR is heavy (PaddleOCR loads ~600MB of models, processes pages serially) and slow (seconds per page). Excel/CSV extraction is fast (milliseconds). Putting them in the same queue means a single scanned PDF blocks 200 lightweight Excel uploads behind it. Celery's `task_routes` config (in [backend/workers/celery_app.py](../backend/workers/celery_app.py)) sends each task to the right queue, and the worker is started with `-Q extraction,mapping,ocr` so all three are served in parallel by separate worker pools.

## Why FastAPI + async SQLAlchemy on the API side, but a sync SQLAlchemy session inside Celery?

FastAPI request handlers are I/O-bound and benefit from asyncio (concurrent DB queries while waiting on network). Celery tasks are CPU/disk-bound (parsing files, running OCR) and asyncio buys nothing. The codebase uses `create_async_engine` for the API (see [backend/shared/db/session.py](../backend/shared/db/session.py)) and a separate `create_engine`-based sync session inside `tasks.py` for workers. Each side picks the right tool.

## Why a monorepo of services rather than one big app?

The original spec (in `.claude/master-prompt.md`) defined eight services — auth, KPI, doc, HR, project, alert, NLP, report, admin. We **deleted seven of them** when it became clear the frontend never called them; they were placeholders. What remains is real code. Keeping the *structure* (separate FastAPI apps per service) means we can scale ingestion independently of KPI, and we can deploy them to separate pods later. The cost today is one extra `main.py` per service, which is cheap.

## Failure modes and what catches them

| Failure | Caught by | Effect |
|---|---|---|
| File too big | [`upload.py`](../backend/services/ingestion_service/routers/upload.py) — magic-byte check + `Content-Length` + streaming size guard | 413 before disk write |
| Unknown MIME | Same router | 415 before extraction queued |
| Extractor crash (corrupt xlsx, encrypted PDF) | Celery `max_retries=2`; `import_record.status` flipped to `extraction_failed` | Frontend polls and shows the error |
| Mapping API down (Anthropic/Gemini) | [`fuzzy_mapper.py`](../backend/services/ingestion_service/mapping/fuzzy_mapper.py) fallback | Lower-quality but functional mapping proposal |
| OCR engine fails to init | Lazy import of `paddleocr` inside `ocr_extractor.py`; failure surfaces as a task failure with low_quality flag | Visible in audit log; user can re-upload as Excel |
| User rolls back commit | `is_archived` flag on `data_records` (soft delete); `archived_by_import_id` records who archived it | Reversible inside `ROLLBACK_WINDOW_DAYS=7` |

## Key design principles

1. **Async pipeline, never blocking the request.** Every long operation (extraction, OCR, mapping, validation) runs in Celery; the API responds in <100 ms with `202 Accepted` and a polling URL.
2. **State machine on the file.** `ImportRecord.status` is the source of truth. Allowed transitions: `pending → extracted → mapping_proposed → mapping_confirmed → validated → committed | cancelled`. The frontend polls this column.
3. **Soft delete, never hard delete.** Rolling back an import flags rows `is_archived=True` and stores `archived_by_import_id`. Audit trail is preserved. Hard deletes are gated behind `Permission.PURGE_FILES`.
4. **Provenance everywhere.** Every committed row links back to the `import_id`; every OCR cell carries its `bounding_box` and `confidence`; every change is an `AuditEntry` with French description and actor user id.
5. **French-first error messages.** Every user-facing message in the ingestion pipeline is in French — required by the Tunisian higher-education context.
