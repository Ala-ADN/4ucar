# 4ucar — Technical Documentation

This folder contains the technical documentation for the **4ucar** university ERP, intended for the technical jury of HACK4UCAR.

Each document covers one part of the system, explains *what* it does, *why* it is designed that way, and *what tradeoffs* were made. Read them in any order, but the suggested path is:

1. [architecture.md](architecture.md) — the 30-second mental model
2. [data-model.md](data-model.md) — what's actually stored, and how
3. [ingestion-service.md](ingestion-service.md) — how data gets into the system
4. [kpi-service.md](kpi-service.md) — how KPIs are computed
5. [workers-and-async.md](workers-and-async.md) — Celery, Redis, queues
6. [auth-and-rbac.md](auth-and-rbac.md) — roles, tenancy, permissions
7. [integrations.md](integrations.md) — external data providers
8. [rag-service.md](rag-service.md) — retrieval-augmented Q&A (scaffold)
9. [frontend.md](frontend.md) — React app
10. [jury-qa.md](jury-qa.md) — anticipated jury questions with answers

## What's actually built (jury-facing summary)

| Layer | Component | Status |
|---|---|---|
| Backend | `ingestion_service` (port 8010) | ✅ Working — upload, extract, OCR, mapping, validation, commit, templates |
| Backend | `kpi_service` (port 8002) | ✅ Working — KPI catalog (Domains A–H), accreditation, professors, recompute |
| Backend | `rag_service` (port 8020) | 🟡 Scaffold only — endpoints declared, bodies unimplemented |
| Workers | Celery (extraction, mapping, ocr queues) | ✅ Working |
| Frontend | React + Vite (port 3000) | ✅ Wired to both backends via Vite proxy |
| Storage | PostgreSQL (TimescaleDB) + Redis | ✅ Running |
| OCR | PaddleOCR PP-StructureV2 (CPU) | ✅ Working |
| ML | sentence-transformers (`intfloat/multilingual-e5-large`), scikit-learn, SHAP | ✅ In dependency tree |

## Top three things to say to the jury

1. **Data ingestion is the hard problem in any KPI ERP.** Every institution has a different Excel template. We solved it with multi-format extractors, OCR with bbox+confidence, and a template-memorization system that auto-confirms recurring uploads.
2. **Data sovereignty is enforced.** OCR runs locally (PaddleOCR), embeddings run locally (`multilingual-e5-large`), mapping has a fully local fuzzy fallback. External APIs (Anthropic / Gemini / OpenAlex) are *enrichment*, never blocking.
3. **The accreditation engine is real.** Domain H evaluates ISO 9001, ISO 21001, and UI GreenMetric using the Vanta/Drata control-test-evidence model. Pure functions over typed inputs — no I/O, fully unit-tested.
