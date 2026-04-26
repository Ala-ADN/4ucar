# Anticipated jury questions — with answers

The questions below are the ones we expect from a technical jury, grouped by theme. Each answer is intentionally short — read them, internalize the *shape* of the answer, then say it in your own words.

---

## Architecture & design

**Q: Why a microservice split when you only have two services running?**
A: We started with eight services from the spec, deleted the six the frontend never called, and kept two real ones plus one scaffold. The split that remains is real: ingestion is heavy, async, and OCR-bound; KPI computation is pure CPU on already-validated rows. Splitting them means we can scale ingestion independently and we can run them on different machine types in production (more disk for ingestion, more CPU for KPI).

**Q: Why FastAPI over Flask / Django REST?**
A: Async-native (matches our async SQLAlchemy and async I/O for file streaming), Pydantic-driven request validation for free, OpenAPI generation for free. Django would force ORM choices; Flask would mean reinventing too much.

**Q: Why Postgres + TimescaleDB instead of a data warehouse like BigQuery / ClickHouse?**
A: Our scale is small (low millions of rows over the network's lifetime). Operational simplicity matters more than analytical scan speed at this stage. TimescaleDB gives us hypertables for `kpi_records` so time-series queries stay fast as data grows, without adding a separate OLAP system.

**Q: How would this scale to 100+ institutions?**
A: Three changes. (1) Run the Celery `ocr` queue on dedicated workers with GPUs — currently CPU. (2) Enable Postgres row-level security so tenant isolation is database-enforced, not application-enforced. (3) Move the network-wide KPI recompute to a Celery beat job triggered nightly instead of per-commit. The architecture is shaped to absorb all three without code rewrites.

---

## Ingestion pipeline

**Q: What's the most complex part of the system?**
A: The ingestion pipeline. Every institution has a different Excel template; OCR adds confidence and bbox metadata that has to flow all the way to the database; validation must be pluggable per KPI field; rollback has to be symmetric. The state machine on `ImportRecord.status` is what holds it together.

**Q: How do you handle a scanned form on a phone photo?**
A: PaddleOCR PP-StructureV2 with bilingual text recognition (FR + AR). Each cell carries a confidence score and a bounding box. Confidence is shown to the user as a green / yellow / red badge per field; cells below 0.60 are not pre-populated and the user sees the source image region next to the field. Bounding boxes are persisted in `data_records.bounding_box` for later auditing.

**Q: What happens if the LLM mapper hallucinates a column-to-field mapping?**
A: The proposal is *never* applied without explicit user confirmation, except when an existing saved template auto-confirms — and template matching is purely local (Jaccard on tokenized headers), no LLM. The LLM is a UX assistant for first-time uploads, never a source of truth.

**Q: How does the template-memorization actually work?**
A: After the first commit, the user can save the column-to-field mapping as a `DocumentTemplate` (name + headers + domain + format). Next upload: we compute Jaccard similarity over de-accented tokenised headers against every template for this institution and domain. Score ≥ 0.6 → auto-confirm; 0.35–0.6 → suggestion; < 0.35 → fall through to LLM mapping. We tried embedding similarity; it doesn't add value at this scale because KPI labels and ministerial form headers reuse the same nouns.

**Q: What if validation fails on row 5 of 1000?**
A: That row goes to `quarantine_rows` with `failure_reason_fr`. The other 999 still commit. The user sees a "5 lignes en quarantaine" badge on the import and can resolve them: correct, override (with justification, requires `Permission.OVERRIDE_QUARANTINE`), or discard.

---

## KPI engine

**Q: How are KPIs defined?**
A: As pure Python functions in [`backend/services/kpi_service/domain/`](../backend/services/kpi_service/domain/), one module per domain (A through H). Each takes a typed dataclass input from `inputs.py` and returns a `KpiResult`. No I/O. Adding a new KPI is one function plus one entry in `DOMAIN_X_CALCULATORS`.

**Q: What's the difference between Domain H and the others?**
A: Domain H (accreditation) is *qualitative*. It returns `ControlEvaluation` per control with status `PASSING / FAILING / NEEDS_EVIDENCE / NOT_APPLICABLE`, not a number. The framework → control → test → evidence model is borrowed from Vanta and Drata. Tests reference KPIs from Domains A–G, document templates, or attestations.

**Q: How do you avoid recomputing every KPI when one cell changes?**
A: The ingestion service publishes `data.committed` on Redis with `(institution_id, period, domain)`. The KPI recompute service subscribes and recomputes only that triple. If a row affects multiple domains it's because the KPI definition genuinely depends on cross-domain data, in which case we recompute both. Network-wide recompute is on-demand only.

**Q: What's the SHAP for?**
A: The international ranking band predictor (`predictor.py`) is planned to be a Ridge regression over per-institution KPI vectors. SHAP gives per-feature attribution so when an institution sees "predicted band: 401–500", they also see *which* KPIs are pushing them down and how much. Model is not trained yet — we don't have labeled historical band data — but the dependency is in place and the interface is decided.

---

## Operations

**Q: How do you deploy this?**
A: Three Dockerfiles in `deploy/docker/` (api, worker, nginx) plus a `docker-compose.yml`. Postgres + Redis as separate services. Production target is Kubernetes — each FastAPI service becomes a Deployment, the Celery worker becomes one or more Deployments per queue, Redis and Postgres are managed.

**Q: What about backups?**
A: Postgres `pg_dump` to S3-compatible storage (Garage in our deploy folder) on a daily cron. `data_records` is the source of truth; `kpi_records` and `accreditation_evaluations` can be recomputed from it. Uploaded files in `uploads/` go to the same backup target.

**Q: How do you monitor the pipeline?**
A: `prometheus-fastapi-instrumentator` is in the dependency tree (mounts `/metrics`). `sentry-sdk` is wired in production for error tracking. `structlog` is used for structured JSON logs. The dashboard the team would build is: queue lengths per Celery queue, p95 task duration per task name, ingestion success rate, OCR confidence distribution.

**Q: What's the blast radius of a bad commit?**
A: Bounded. Soft-delete on `data_records` with `is_archived` and `archived_by_import_id` means rollback inside the `ROLLBACK_WINDOW_DAYS=7` window restores prior state exactly. Hard delete requires `Permission.PURGE_FILES`. `audit_entries` is append-only and survives rollback.

---

## Data sovereignty & privacy

**Q: Are you sending student data to OpenAI / Anthropic / Google?**
A: No. The mappers receive *column headers*, not row data. Embeddings run locally (`intfloat/multilingual-e5-large`). OCR runs locally (PaddleOCR). The only external APIs in the hot path are the LLM mapper (which sees only headers) and OpenAlex (which sees only published faculty information that's already public). Cell values never leave Postgres.

**Q: What's your fallback if the network is down?**
A: Ingestion still works end-to-end. Mapping uses the local fuzzy fallback (`difflib.get_close_matches` against a static alias dictionary). KPI computation never depended on the network. The only thing that breaks is OpenAlex enrichment of faculty profiles, which is not on the user's interactive path.

---

## RAG service

**Q: Why is the RAG service a scaffold?**
A: Three reasons. The interface is the load-bearing part — Pydantic schemas, route signatures, RBAC hook, and source taxonomy are pinned in code. The implementation is mechanical once the interface is fixed. The real reason to defer was: indexing makes sense only after we have meaningful data, and the demo's seeded slice is small. We didn't want to debug embedding-model downloads live during a jury demo.

**Q: How would you prevent hallucinations in the RAG answers?**
A: System prompt in [prompts/rag/system_prompt.md](../prompts/rag/system_prompt.md) explicitly forbids inventing facts and mandates `[source:chunk_id]` citations. The frontend would show each citation as a clickable link back to the source row or document. If the retrieved context doesn't answer, the model is instructed to refuse in French.

---

## Things to deflect cleanly

If the jury asks about something we didn't build (alert engine, report PDF generation, RAG bodies, ML predictor training), the honest answer is:

> "The interface is in place — the {worker / module / scaffold} is in the repo with typed inputs and outputs. We chose to keep that out of this build because {it depended on data we don't yet have, or it would have stolen time from the parts that demonstrate the architecture}. Implementing it is mechanical from here."

Don't oversell. The strength of this system is that **what's built, works**: 47 unit + integration tests pass, the live demo runs end-to-end on real Excel files, the KPI engine produces real numbers from real `data_records`. That's the story.
