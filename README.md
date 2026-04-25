# 4ucar — UCAR Intelligent University ERP

Backend monorepo. See [.claude/master-prompt.md](.claude/master-prompt.md) for the full
product specification.

## Layout

```
backend/
├── shared/         # config, db, auth, tenancy, storage, cache, schemas
├── models/         # SQLAlchemy ORM models (one module per aggregate)
├── services/       # FastAPI service apps — one subpackage per service
│   ├── auth_service/
│   ├── kpi_service/
│   ├── doc_service/
│   ├── hr_service/
│   ├── project_service/
│   ├── alert_service/
│   ├── nlp_service/
│   ├── report_service/
│   ├── admin_service/
│   └── gateway/    # local-dev aggregator that mounts every router
├── workers/        # Celery workers + beat schedule
└── migrations/     # Alembic
deploy/             # docker-compose, Dockerfiles, .env.example
prompts/            # versioned LLM prompt templates
scripts/            # operational scripts
tests/              # unit / integration / e2e
```

## Status

This is a **structural scaffold only** — every function body is `NotImplementedError`
or empty. Dependencies are declared without version pins; pin in CI / production
overrides as the API surface stabilises.
