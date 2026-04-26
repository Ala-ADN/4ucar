# UCAR Intelligent University ERP — Claude Code Session Guide

> Version: 2.0 · April 2026 · Living document

---

## What This Is

A university management platform for the University of Carthage (UCAR), Tunisia. UCAR oversees 35+ affiliated institutions with no existing centralized digital system. The platform's primary business purpose is to enable UCAR institutions to compete in international university rankings (QS, THE, Shanghai, UI GreenMetric) by building a verified, time-series KPI database.

All code runs on UCAR's own private servers. No institutional data may be processed by external cloud services in production. Tunisian data protection law (Loi organique 2004-63) applies. The audit trail is a legal requirement.

---

## Architecture

Microservices. Each service is its own FastAPI process with its own database access. Services communicate via Redis pub/sub events after writes — they do not call each other directly during request processing.

```
API Gateway (nginx)
    ├── ingestion_service   ← data entry point, THIS IS WHAT WE ARE BUILDING NOW
    ├── kpi_service         ← KPI computation + ranking
    ├── doc_service         ← document classification + OCR (general docs)
    ├── hr_service          ← professor profiles + workload + hiring
    ├── project_service     ← project matching
    ├── alert_service       ← threshold monitoring + notifications
    ├── nlp_service         ← natural language queries (RAG)
    ├── report_service      ← scheduled PDF/Excel reports
    └── admin_service       ← tenant provisioning + user management
```

**Data layer:** PostgreSQL (asyncpg), Redis (Celery + cache + pub/sub), local disk → MinIO (production).

---

## Tech Stack — Non-Negotiable

- **Language:** Python 3.12
- **Framework:** FastAPI (async)
- **Package manager:** UV only. Never pip.
- **Database:** PostgreSQL with async SQLAlchemy (asyncpg). Never SQLite.
- **Task queue:** Celery + Redis. No Kafka, no RabbitMQ.
- **OCR:** PaddleOCR with PP-StructureV2 (not basic OCR, not Tesseract for this service)
- **AI mapping:** Anthropic SDK → claude-sonnet-4-6 (prototype only; local embeddings in production)
- **File store:** Local `uploads/` directory → MinIO in production

---

## Project Structure

```
backend/
├── services/
│   ├── ingestion_service/   ← PRIMARY FOCUS — see data-injestion.md
│   ├── doc_service/
│   ├── hr_service/
│   ├── kpi_service/
│   ├── nlp_service/
│   ├── project_service/
│   ├── report_service/
│   ├── admin_service/
│   └── gateway/
├── models/                  ← shared SQLAlchemy models (platform-wide)
├── shared/
│   ├── auth/                ← JWT decode + RBAC
│   ├── cache/               ← Redis client
│   ├── db/                  ← async engine, session factory, RLS helpers
│   ├── schemas/             ← shared Pydantic schemas
│   ├── storage/             ← MinIO + Elasticsearch clients
│   ├── tenancy/             ← tenant context middleware
│   ├── config.py            ← base Settings (pydantic-settings)
│   ├── exceptions.py        ← UcarError hierarchy
│   ├── logging.py           ← structured JSON logger
│   └── audit.py             ← audit log writer
└── workers/
    ├── celery_app.py        ← Celery app factory
    └── ingestion_worker.py  ← ingestion-specific tasks (now in ingestion_service/tasks.py)
deploy/
    ├── docker-compose.yml
    ├── .env.example
    └── docker/
tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## Coding Standards

- Python 3.12 type hints everywhere. Pydantic v2 for all schemas.
- Async all the way down. No blocking I/O in FastAPI handlers.
- Heavy work (extraction, OCR, Claude calls, normalization) → Celery workers only.
- FastAPI handlers: receive, validate auth, enqueue, return — never block.
- Error messages to users: French only. No English stack traces exposed.
- Structured JSON logging via `structlog` on every significant pipeline event.
- No comments that explain WHAT the code does. Comments only for non-obvious WHY.
- No unused imports, no dead code.
- SQLAlchemy models use `mapped_column` + `Mapped[]` (2.0 style).

---

## Key Files to Know

| File                                               | Purpose                                   |
| -------------------------------------------------- | ----------------------------------------- |
| `.claude/data-injestion.md`                        | Ingestion service detailed spec           |
| `.claude/kpi.md`                                   | KPI catalog and ranking weights           |
| `.claude/hack4ucar.md`                             | Hackathon context and constraints         |
| `backend/services/ingestion_service/kpi_schema.py` | Single source of truth for all KPI fields |
| `backend/services/ingestion_service/validator.py`  | All business validation rules             |
| `backend/services/ingestion_service/tasks.py`      | Celery task definitions                   |
| `backend/shared/auth/rbac.py`                      | Role/permission matrix                    |
| `deploy/.env.example`                              | All environment variable names            |

---

## Current Status (April 2026)

The ingestion service is fully implemented (see `backend/services/ingestion_service/`). Other services have scaffolding stubs only. Work should continue in this order:

1. ✅ Ingestion service (complete)
2. KPI computation service (`kpi_service/`)
3. Auth service (JWT issuance, Keycloak integration)
4. HR service (professor profiles, workload, hiring)
5. Alert service (threshold monitoring)
6. NLP service (RAG queries)
7. Report service (PDF/Excel generation)
8. Admin service (tenant provisioning)
9. Frontend (React + TypeScript)

---

## Multi-Tenancy

Every database table that holds institution data has a `institution_id` (UUID) column. PostgreSQL RLS enforces isolation at DB level. The application layer sets `app.current_tenant` from JWT claims at session start. Cross-institution queries require `GLOBAL_READ` permission.

---

## Testing Philosophy

- pytest + httpx AsyncClient
- Separate in-memory or test-schema database (never touch production)
- Mock Claude API and PaddleOCR in tests — no real external calls
- Test fixture files in `tests/fixtures/`: clean Excel, malformed Excel (merged cells), semicolon CSV, table image
- Cover: happy paths, each validation rule category, auth enforcement, conflict modes, quarantine flows

---

## What Never Changes

- UV for package management
- PostgreSQL (not any NoSQL)
- Redis (not any other broker)
- PaddleOCR PP-StructureV2 (not basic OCR, not Tesseract) for the ingestion service
- All institutional data stays on UCAR servers
- Audit table is append-only — no UPDATE or DELETE on audit rows
- Source files retained on disk ≥ 12 months
