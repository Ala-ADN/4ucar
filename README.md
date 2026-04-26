<div align="center">

# 4UCAR

### **The Intelligent University ERP for the University of Carthage**

_Turning 35+ disconnected institutions into a verified, ranking-ready KPI engine._

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791.svg)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-Redis-37814A.svg)](https://docs.celeryq.dev/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-PP--StructureV2-FF6B35.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Status](https://img.shields.io/badge/status-active--build-yellow.svg)]()

</div>

---

## Vision

**UCAR oversees 35+ affiliated institutions with no centralized digital system.** Every ranking submission today is a frantic month of spreadsheet archaeology.

4UCAR replaces that with a single source of truth: a verified, time‑series KPI database that lets UCAR institutions compete in **QS, THE, Shanghai, and UI GreenMetric** rankings — and prove compliance against **ISO 9001**, **ISO 21001**, and **GreenMetric** frameworks — _automatically, from the documents they already produce_.

> **Sovereignty first.** All code runs on UCAR's private servers. No institutional data leaves the country. Tunisian Loi organique 2004‑63 applies. The audit trail is a legal requirement, not a feature.

---

## Architecture

A microservice mesh where each service owns its database access and talks to peers via **Redis pub/sub events** — never direct calls. Writes broadcast, readers react.

```
                         ┌────────────────────────┐
                         │   API Gateway (nginx)  │
                         └───────────┬────────────┘
                                     │
   ┌─────────────┬─────────────┬─────┴───────┬─────────────┬─────────────┐
   │             │             │             │             │             │
┌──▼───┐    ┌────▼───┐    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
│ ing- │    │  kpi   │    │   doc   │   │   hr    │   │ project │   │  alert  │
│ est  │    │service │    │ service │   │ service │   │ service │   │ service │
└──┬───┘    └────┬───┘    └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
   │             │             │             │             │             │
   └─────────────┴─────────────┴──── Redis pub/sub ────────┴─────────────┘
                                     │
                  ┌──────────────────┼──────────────────┐
                  │                  │                  │
             ┌────▼────┐        ┌────▼────┐       ┌─────▼─────┐
             │   nlp   │        │ report  │       │   admin   │
             │ service │        │ service │       │  service  │
             └─────────┘        └─────────┘       └───────────┘
```

| Layer       | Tech                                                    |
| ----------- | ------------------------------------------------------- |
| API         | FastAPI (async) · Pydantic v2 · Python 3.12             |
| Persistence | PostgreSQL with row‑level security (asyncpg/SQLAlchemy) |
| Async Work  | Celery + Redis (broker, cache, pub/sub)                 |
| OCR         | PaddleOCR PP‑StructureV2 (structured tables + bboxes)   |
| AI Mapping  | Claude Sonnet 4.6 (prototype) → local `multilingual-e5` |
| Files       | Local disk → Garage in production                       |
| Packaging   | **UV**                                                  |

---

## Data Ingestion Pipeline

> _The single entry point for every structured fact in the platform._

The ingestion service consumes Excel, CSV, PDF, and image uploads — extracts, validates, normalizes, and commits them as immutable KPI records. Every transition is **user‑triggered**: nothing advances on its own.

```
   Upload  ─►  extracted  ─►  mapping_proposed  ─►  mapping_confirmed  ─►  validated  ─►  committed
                                                                            │
                                                                            └──►  quarantine (manual review)
```

| #   | Stage                | From                | To                  | Trigger          |
| --- | -------------------- | ------------------- | ------------------- | ---------------- |
| 1   | Receive & enqueue    | —                   | `pending`           | `POST /upload`   |
| 2   | Extraction           | `pending`           | `extracted`         | Celery (auto)    |
| 3   | AI column mapping    | `extracted`         | `mapping_proposed`  | `GET /mapping`   |
| 4   | User confirms        | `mapping_proposed`  | `mapping_confirmed` | `POST /mapping`  |
| 5   | Normalize + validate | `mapping_confirmed` | `validated`         | Celery (auto)    |
| 6   | Quarantine review    | `validated`         | —                   | optional, manual |
| 7   | Commit               | `validated`         | `committed`         | `POST /commit`   |

**Highlights**

- **PaddleOCR PP‑StructureV2** with per‑cell bounding boxes — the frontend can highlight the exact source region when a reviewer hovers over an extracted value.
- **Privacy‑preserving Claude mapping** — only column headers ever leave the server, never row data. Drop‑in replacement to a local embedding model is a one‑file change.
- **Quarantine is hard** — invalid rows never enter the KPI store automatically. Only `ucar_analyst` or `super_admin` can override, and every override is audited.
- **Three commit conflict modes**: `overwrite` (archive + replace), `merge` (delta only), or `cancel` (409, no writes).
- **Append‑only audit log.** No UPDATE, no DELETE, no exceptions. Source files retained ≥ 12 months.

After every successful commit, an event hits Redis:

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

…which fans out to the KPI service, the alert service, and — most powerfully — the accreditation engine.

---

## Accreditation Engine

> _Vanta for universities. Drata for ISO 21001. The compliance posture that updates itself._

Most accreditation tools predict a score. **4UCAR doesn't.** It answers exactly one question per control:

> _"Do we have sufficient, approved evidence that this requirement is currently met — and if not, what's missing?"_

### Core loop

```
   Framework  ─►  Controls  ─►  Tests  ─►  Evidence  ─►  approved Documents + computed KPIs
        ▲                                                                  │
        └──────────── status updates in real time ◄────────────────────────┘
```

Every document template carries a list of `linked_test_ids`. The moment a reviewer approves a `grade_sheet`, evidence is auto‑created for every test that template satisfies, the parent control is re‑evaluated, and the dashboard updates over WebSocket. **Every document approval is a compliance event.**

### Frameworks shipped

| Code          | Name                             | Scope       | Notes                                             |
| ------------- | -------------------------------- | ----------- | ------------------------------------------------- |
| `ISO9001`     | ISO 9001:2015 Quality Management | INSTITUTION | Foundational QMS — 10 clauses                     |
| `ISO21001`    | ISO 21001:2018 Educational Orgs  | INSTITUTION | EOMS — extends 9001 for education, 12 clauses     |
| `GREENMETRIC` | UI GreenMetric World Rankings    | NETWORK     | 6 categories — energy, waste, water, transport, … |

### Status semantics (industry‑aligned)

| Status           | Color | Meaning                                                              |
| ---------------- | ----- | -------------------------------------------------------------------- |
| `PASSING`        | Green | All required tests pass; evidence on file and approved               |
| `FAILING`        | Red   | Required tests failing; evidence missing or below threshold          |
| `NEEDS_EVIDENCE` | Amber | Test defined, no evidence yet — pre‑failing, not the same as failing |
| `NOT_APPLICABLE` | Grey  | Explicitly waived with documented reason and audit trail             |

### Sample dashboard

```
┌──────────────────────────────────────────────────────────────┐
│  Accreditation & Framework Compliance                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │  ISO 9001    │  │  ISO 21001   │  │  UI GreenMetric   │   │
│  │  ████████    │  │  ██████░░    │  │  ████░░░░         │   │
│  │    8/10      │  │    8/12      │  │     4/6           │   │
│  │  PASSING     │  │  FAILING     │  │  FAILING          │   │
│  └──────────────┘  └──────────────┘  └───────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

**Gap analysis is sorted by impact** — `control_weight × (1 − current_progress)` descending — so the next action is always the highest‑leverage one.

---

## Tech Stack — Non‑Negotiable

```yaml
language: Python 3.12 (full type hints, Pydantic v2 schemas)
framework: FastAPI (async all the way down — no blocking I/O in handlers)
package_manager: UV # never pip
database: PostgreSQL # never SQLite, never NoSQL
queue: Celery + Redis # no Kafka, no RabbitMQ
ocr: PaddleOCR PP-StructureV2
ai_mapping: Anthropic SDK → claude-sonnet-4-6 (prototype only)
files: local uploads/ → Garage (prod)
errors_to_users: French only # no English stack traces leak
logging: structured JSON via structlog
audit: append-only — no UPDATE, no DELETE on audit rows
```

---

## Multi‑Tenancy

Every institution‑scoped table carries `institution_id UUID`. PostgreSQL **row‑level security** enforces isolation at the database layer; the application sets `app.current_tenant` from the JWT claims at session start. Cross‑institution reads require the `GLOBAL_READ` permission — and that's logged too.

---

## Project Structure

```
backend/
├── services/
│   ├── ingestion_service/   # ◄ shipped — see .claude/data-injestion.md
│   ├── kpi_service/
│   ├── doc_service/
│   ├── hr_service/
│   ├── project_service/
│   ├── alert_service/
│   ├── nlp_service/
│   ├── report_service/
│   ├── admin_service/
│   └── gateway/
├── shared/                  # auth, cache, db, schemas, storage, tenancy, audit
├── models/                  # SQLAlchemy 2.0 (mapped_column / Mapped[...])
├── workers/                 # Celery app + beat schedule
└── migrations/              # Alembic
deploy/                      # docker-compose, Dockerfiles, .env.example
prompts/                     # versioned LLM prompt templates
scripts/                     # operational scripts
tests/                       # unit / integration / e2e
FrontEnd/                    # React + TypeScript client
```

---

## Quick Start

```bash
# 1. Install dependencies (UV only — no pip)
uv sync

# 2. Bring up Postgres, Redis, Garage
docker compose -f deploy/docker-compose.yml up -d

# 3. Run migrations
uv run alembic upgrade head

# 4. Start the ingestion service
uv run uvicorn backend.services.ingestion_service.main:app --reload

# 5. Start the workers (in separate terminals)
uv run celery -A workers.celery_app worker -Q extraction
uv run celery -A workers.celery_app worker -Q ocr -c 2
uv run celery -A workers.celery_app worker -Q mapping
```

The frontend lives in [FrontEnd/](FrontEnd/) — `npm install && npm run dev`.

---

## Roadmap

| #   | Service                  | Status      |
| --- | ------------------------ | ----------- |
| 1   | Ingestion service        | **shipped** |
| 2   | KPI computation service  | next        |
| 3   | Auth (JWT + Keycloak)    | planned     |
| 4   | HR service               | planned     |
| 5   | Alert service            | planned     |
| 6   | NLP / RAG service        | planned     |
| 7   | Report service           | planned     |
| 8   | Admin / tenant provision | planned     |
| 9   | Frontend (React + TS)    | in progress |

---

## Documentation Map

| File                                                           | What lives there                           |
| -------------------------------------------------------------- | ------------------------------------------ |
| [.claude/master-prompt.md](.claude/master-prompt.md)           | Full session guide & coding standards      |
| [.claude/data-injestion.md](.claude/data-injestion.md)         | Ingestion service implementation reference |
| [.claude/accreditation.md](.claude/accreditation.md)           | Accreditation engine specification         |
| [.claude/kpi.md](.claude/kpi.md)                               | KPI catalog and ranking weights            |
| [.claude/professor-matching.md](.claude/professor-matching.md) | HR matching design                         |
| [.claude/project-matching.md](.claude/project-matching.md)     | Project matching design                    |
| [.claude/hack4ucar.md](.claude/hack4ucar.md)                   | Hackathon context and constraints          |
| [DEMO.md](DEMO.md)                                             | Demo script                                |

---

**Built for the University of Carthage from University of Carthage**
_Sovereign · Auditable · Ranking‑ready_

</div>
