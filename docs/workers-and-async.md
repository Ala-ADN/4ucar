# Workers & async pipeline

**Path:** [backend/workers/](../backend/workers/) and [backend/services/ingestion_service/tasks.py](../backend/services/ingestion_service/tasks.py)

## Why workers at all

Three operations in the ingestion pipeline are slow:

1. **OCR** — PaddleOCR loads ~600 MB of model weights on first call; processing a single page is hundreds of ms to several seconds.
2. **PDF rendering** — rasterizing pages from a 30-page PDF for OCR is seconds.
3. **LLM mapping** — Anthropic/Gemini round-trip is ~2–5 s; with retries that's ~15 s budget.

Holding an HTTP request open for 15+ seconds breaks browsers and load balancers. Celery moves all of that off the request thread. The API responds in <100 ms with `202 Accepted` and a polling URL; the work happens in the background.

## Topology

```
                     ┌───────────────────────┐
       enqueue       │     Redis (broker)    │   poll status
   ──────────────►   │  db1: celery broker   │   ◄───────────────
                     │  db2: celery results  │
                     └───────────┬───────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
     ┌────────────┐       ┌────────────┐       ┌────────────┐
     │ extraction │       │  mapping   │       │    ocr     │
     │   queue    │       │   queue    │       │   queue    │
     └─────┬──────┘       └─────┬──────┘       └─────┬──────┘
           │                    │                    │
   run_extraction          run_mapping       run_ocr_extraction
   run_normalization_      (Gemini/Claude    (PaddleOCR
    and_validation          + fuzzy fallback) PP-StructureV2)
```

All three queues are consumed by **a single worker process** started with `-Q extraction,mapping,ocr`. Celery's worker concurrency is configured per-queue at the `worker_prefetch_multiplier=1` level so a long-running OCR task doesn't starve the lighter queues.

## Configuration — [celery_app.py](../backend/workers/celery_app.py)

```python
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Tunis",            # local time for scheduled jobs
    enable_utc=True,
    task_track_started=True,            # frontend can show "running" not just "pending"
    task_acks_late=True,                # retry semantics on worker crash
    worker_prefetch_multiplier=1,       # don't grab a second slow task while one is running
    task_routes={
        "...run_extraction":            {"queue": "extraction"},
        "...run_ocr_extraction":        {"queue": "ocr"},
        "...run_mapping":               {"queue": "mapping"},
        "...run_normalization_and_validation": {"queue": "extraction"},
    },
    task_default_queue="extraction",
)
```

`task_acks_late=True` matters: it means a task is acknowledged only after success. If a worker crashes mid-OCR (PaddleOCR has been known to segfault on edge cases), Redis re-queues the task and another worker picks it up.

## Tasks — [ingestion_service/tasks.py](../backend/services/ingestion_service/tasks.py)

All four tasks share a pattern:

```python
@celery_app.task(bind=True, name="...", max_retries=2)
def run_xxx(self, import_id: str) -> dict:
    with _get_sync_session() as session:
        record = session.get(ImportRecord, uuid.UUID(import_id))
        if not record:
            return {"error": "import not found"}

        record.status = "running_xxx"
        session.commit()
        try:
            # ... do work, write result fields on `record` ...
            record.status = "next_state"
            session.commit()
            return {"ok": True}
        except Exception as e:
            record.status = "xxx_failed"
            record.error_message = str(e)
            session.commit()
            raise self.retry(exc=e, countdown=5) if self.request.retries < 2 else e
```

### Why a sync session inside the worker

The API uses `create_async_engine` because handlers are I/O-bound and benefit from `await`. Workers are CPU/disk-bound; asyncio gives nothing back. A separate **synchronous** engine (`_sync_engine` lazily built from `settings.postgres_dsn_sync` — the `postgresql+psycopg://` form, not `+asyncpg://`) keeps worker code straightforward and avoids dragging an event loop into Celery.

## Other workers (placeholders)

The repo also contains:

| File | Purpose | Status |
|---|---|---|
| `kpi_compute_worker.py` | Future: heavy network-wide recompute jobs | Stub |
| `migration_worker.py` | Future: Alembic upgrades + back-fills as scheduled jobs | Stub |
| `alert_worker.py` | Future: threshold-driven alerts (KPI dropped >10% YoY) | Stub |
| `report_worker.py` | Future: WeasyPrint PDF generation for MESRS submissions | Stub |
| `beat_schedule.py` | Future: cron schedule for the workers above | Stub |

These files exist so the structure is visible; they are not imported by the running celery app (only `ingestion_service.tasks` is in the `include=[]` list). When implemented, each adds one entry to `celery_app.conf.beat_schedule` and one line to `include`.

## What you'll be asked

- *"Why Celery and not RQ / Dramatiq / asyncio.create_task?"* — Celery is the only option that gives us per-queue routing + late acks + retries + a beat scheduler in one package, and it's the most widely understood. RQ is simpler but lacks routing; Dramatiq is a good alternative we'd consider in production.
- *"What if Redis dies?"* — the API surface keeps working for everything that doesn't enqueue (reads, audit, templates). New uploads return `503` because `apply_async` fails. Already-queued tasks are durable: Redis `appendonly` mode (configured in deploy/docker-compose.yml) means restart recovers the queue.
- *"Why three queues and not three workers?"* — at this scale (one host, prototype) one worker process serving all three queues is cheaper. In production you split: small fast pool for extraction+mapping, dedicated OCR pool with longer task timeouts and bigger memory limits.
- *"How do you handle a stuck task?"* — Celery has `task_time_limit` (hard kill) and `task_soft_time_limit` (raises a `SoftTimeLimitExceeded` the task can catch and clean up after). Both should be set per-task in production; the prototype relies on Postgres pool timeouts to surface dead tasks.
