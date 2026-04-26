# Data Model

**Migrations:** [backend/migrations/versions/](../backend/migrations/versions/)
**Active models:** [backend/services/ingestion_service/models/](../backend/services/ingestion_service/models/) and [backend/models/](../backend/models/)

## Storage stack

- **PostgreSQL with TimescaleDB extension** — primary OLTP + time-series for `kpi_records` (institution × period). TimescaleDB lets us declare `kpi_records` as a hypertable partitioned on `period`, which keeps queries on "the latest period" and "year-over-year" cheap as the table grows.
- **Redis** — pub/sub on channel `data.events`, plus broker (db1) and result backend (db2) for Celery.
- **Filesystem** — `uploads/{import_id}/{filename}` for raw uploaded files. We chose disk over S3/Garage for the prototype because it removes one moving part from the demo. The `boto3` and Garage configs in `deploy/` are ready when we want them.
- **Elasticsearch** (declared but not active) — intended for full-text search over historical documents.

## The four migrations

| Migration | What it creates |
|---|---|
| `001_ingestion_tables.py` | `import_records`, `data_records`, `quarantine_rows`, `data_requests`, `data_request_responses`, `locked_periods`, `audit_entries` |
| `002_document_templates.py` | `document_templates` (saved column-to-field mappings, scored against new uploads by [templates_matcher.py](../backend/services/ingestion_service/templates_matcher.py)) |
| `003_kpi_records.py` | `kpi_records` (computed values), `accreditation_evaluations`, `framework_definitions` |
| `20260426_0000_initial_hr_schema.py` | `professors`, `publications`, `coauthorships`, `enrichment_runs` |

## Core tables (ingestion side)

### `import_records` — the state machine row

One row per upload attempt. The full pipeline state lives here. From [models/import_record.py](../backend/services/ingestion_service/models/import_record.py):

```
id (uuid)              institution_id    uploaded_by
original_filename      storage_path      file_size_bytes      detected_mime_type
domain                 period            is_historical
status                 ←── pending → extracted → mapping_proposed → mapping_confirmed
                            → validated → committed | cancelled
extraction_task_id     mapping_task_id   validation_task_id

extracted_headers      extracted_preview     sheet_name        total_rows
mapping_proposal       confirmed_mapping
validation_summary     normalization_log
overwrite_mode

records_valid          records_warned        records_quarantined    records_committed

created_at             updated_at            committed_at           cancelled_at
```

The frontend polls `GET /imports/{id}/status` and reads only `status` + the `records_*` counters. The whole UX is driven from this column.

### `data_records` — the committed values

One row per `(institution, period, KPI field)` value. This is what the KPI service reads.

```
id, import_id (FK), institution_id, period, domain, field_id
raw_value, normalized_value (JSON)
is_warned, warning_message
ocr_confidence, bounding_box (JSON: {x,y,w,h,page})  ← null for non-OCR sources
is_archived, archived_at, archived_by_import_id      ← soft delete for overwrite/rollback
committed_at
```

Archive semantics: an `overwrite` commit flags prior overlapping rows `is_archived=True` and writes the new `import_id` as `archived_by_import_id`. Rolling back an import flips them back. Indexes on `institution_id`, `period`, `field_id`, and `is_archived` keep KPI queries fast.

### `quarantine_rows` — failed-validation rows held for review

```
id, import_id (FK), row_index, raw_data (JSON)
failed_field, failure_reason_fr
resolution (correct | override | discard)
corrected_value, resolved_by, resolved_at
override_justification
```

`override_justification` is mandatory when `resolution == "override"` — required by `Permission.OVERRIDE_QUARANTINE` semantics and surfaced in the audit report.

### `audit_entries`

Every state transition writes an `AuditEntry`:

```
id, import_id, institution_id, user_id
action (enum: FILE_UPLOADED | EXTRACTION_COMPLETE | MAPPING_PROPOSED | ...)
description_fr (free-text French description)
created_at
```

This is the table MESRS auditors read. Every row is in French because that's what they read.

### `data_requests` and `data_request_responses`

UCAR central pushes "I need 2026-S1 academic data from these 12 institutions by Friday" requests. Each targeted institution has a response row tracking `not_started | in_progress | submitted | late`, optionally linking to the `import_id` they used to satisfy the request.

### `locked_periods`

Once a period is reported to MESRS, super_admin locks it. Further uploads to that `(institution, period [, domain])` are rejected. Only `Permission.UNLOCK_PERIOD` can clear the lock.

## Core tables (KPI side)

### `kpi_records` — TimescaleDB hypertable

```
institution_id, period, domain, kpi_id
value, status (OK | INSUFFICIENT_DATA | OUT_OF_RANGE)
target, computed_at
```

Hypertable partitioned on `period`. A query like "INSAT's research KPIs for 2026-S1" is a tight index range scan; "every institution's RES-04 over 5 years" hits one chunk per year and parallelises naturally.

### `framework_definitions` and `accreditation_evaluations`

Reference data for ISO 9001, ISO 21001, GreenMetric. Updated through code-versioned changes to [`frameworks.py`](../backend/services/kpi_service/domain/frameworks.py), then synced to the table by a script. Evaluations are one row per `(institution, framework, control)` carrying status, evidence pointers, computed_at.

### `professors` and friends

```
professors            ─── one row per faculty member
publications          ─── one row per work, link to professor by ORCID/openalex_id
coauthorships         ─── network edges
enrichment_runs       ─── audit of which provider was called when (OpenAlex / Scholar)
```

This is where the OpenAlex enrichment lands. See [integrations.md](integrations.md).

## Tenancy

Every table that contains institution-specific data has an `institution_id` column. The plan was Postgres **row-level security** (RLS) for hard tenant isolation; the scaffold for it lives in [shared/db/rls.py](../backend/shared/db/rls.py) but is not enabled in this build. **Today, tenancy is enforced in application code**: [`require_own_institution()`](../backend/services/ingestion_service/dependencies.py) is called in every router that takes an `institution_id` parameter, and rejects requests where the caller's role is institution-scoped and the path doesn't match.

## What you'll be asked

- *"Why TimescaleDB instead of regular Postgres?"* — `kpi_records` is genuinely time-series. Hypertables give us automatic partitioning + chunk pruning + continuous aggregates (e.g. precomputed yearly rollups). Without it, the `period`-range queries the dashboard needs would scan a growing table.
- *"How do you guarantee data integrity across the multi-step pipeline?"* — every transition is a single Postgres transaction; intermediate state is on the `import_record` row; on commit, all `data_records` insert in one transaction; if the transaction aborts, nothing changes. Celery `task_acks_late=True` retries the *task*, not the partial DB state.
- *"What happens to a soft-deleted row when its import is rolled back?"* — un-archived (back to `is_archived=False`); the rollback is symmetric. Hard deletes never happen automatically — they require `Permission.PURGE_FILES` and an explicit endpoint call.
- *"Where is the audit trail for who looked at what?"* — `audit_entries` covers *write* actions. Read auditing (who downloaded which file) is on the roadmap; today it's in nginx access logs only.
