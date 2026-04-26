# UCAR Intelligent University ERP — Master Project Document

> **Status:** Living document — v1.0 · April 2026  
> **Owner:** HACK4UCAR Core Team  
> **Scope:** Full platform specification for Claude Code implementation  
> **Classification:** Internal — Engineering Reference

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Service Map](#3-service-map)
4. [Module 1 — KPI Engine & Ranking Dashboard](#4-module-1--kpi-engine--ranking-dashboard)
5. [Module 2 — Document Ingestion & Migration Pipeline](#5-module-2--document-ingestion--migration-pipeline)
6. [Module 3 — Professor & Staff Management](#6-module-3--professor--staff-management)
7. [Module 4 — Project Matching Dashboard](#7-module-4--project-matching-dashboard)
8. [Module 5 — Alerts & Compliance Engine](#8-module-5--alerts--compliance-engine)
9. [Module 6 — Nice-to-Have Features](#9-module-6--nice-to-have-features)
10. [Data Models](#10-data-models)
11. [API Contract Reference](#11-api-contract-reference)
12. [Multi-Tenancy & Security](#12-multi-tenancy--security)
13. [Deployment Topology](#13-deployment-topology)
14. [Implementation Roadmap](#14-implementation-roadmap)
15. [Open Questions & Constraints](#15-open-questions--constraints)

---

## 1. Project Overview

### 1.1 Problem Statement

The University of Carthage (UCAR) oversees 35 affiliated institutions operating as disconnected silos. There is no centralized digital governance layer: data lives in paper records, scattered Excel files, and incompatible per-institution tools. This creates three acute failure modes:

| Failure Mode           | Observable Symptom                                                                                 | Business Impact                                                  |
| ---------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| No KPI system          | Performance is measured informally, subjectively, inconsistently                                   | Poor resource allocation, zero ranking signal, no accountability |
| No document management | Critical institutional records (syllabi, budgets, payslips, inventories) are inaccessible at scale | Compliance gaps, audit failures, inability to compute KPIs       |
| No HR intelligence     | Professor matching, workload balance, and hiring are manual and opaque                             | Misaligned faculty, workflow inequity, legal risk                |

### 1.2 Vision

> A centralized, AI-powered university ERP that computes internationally-aligned KPIs from live documents, ranks institutions transparently, manages human resources intelligently, matches projects by institutional merit, and escalates compliance risks before they become crises.

### 1.3 Core Design Principles

- **KPI-first**: Every module feeds the KPI engine. The dashboard is the product's center of gravity.
- **Document-native**: All metrics derive from ingested, parsed, and structured documents — not manual entry.
- **Multi-tenant by default**: Every query, every record, every API call is scoped to a `tenant_id` (institution). Cross-tenant aggregation is a privileged operation.
- **Explainable by design**: Every KPI score, every alert, every ranking delta must carry a human-readable rationale and a data lineage pointer.
- **Offline-tolerant reads**: The last 24h of computed KPIs are cached locally. Network degradation must not break dashboards.
- **Bilingual throughout**: All UI strings, reports, alert messages, and chatbot responses support French and Arabic (RTL).

### 1.4 Stakeholder Map

| Role                 | Primary Module                 | Key Need                                                |
| -------------------- | ------------------------------ | ------------------------------------------------------- |
| University President | KPI Dashboard, Alerts, Accreditation | Consolidated cross-institution view, accreditation posture |
| Dean / Director      | KPI Dashboard, Alerts          | Institution-level KPIs vs. UCAR benchmarks              |
| Administrative Staff | Document Ingestion, HR         | Efficient document upload, request tracking             |
| Faculty Member       | HR Dashboard, Project Matching | Workload visibility, project assignment transparency    |
| HR Manager           | Professor Management           | Hiring automation, workload balancing                   |
| Finance Officer      | KPI Dashboard                  | Budget vs. actual, cost-per-student                     |
| IT Administrator     | All modules                    | Tenant config, user management, audit logs              |
| MESRS Auditor        | KPI Dashboard, Reports         | Standardized compliance exports                         |

---

## 2. Architecture Overview

### 2.1 System Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│  Web App (React)  ·  Mobile App (React Native)  ·  Admin CLI   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS / WebSocket
┌───────────────────────────▼─────────────────────────────────────┐
│                      API Gateway                                │
│  Auth (JWT + RBAC)  ·  Rate Limiting  ·  Tenant Routing        │
└──┬────────┬─────────┬──────────┬─────────┬──────────┬──────────┘
   │        │         │          │         │          │
┌──▼──┐ ┌──▼──┐  ┌───▼───┐  ┌──▼──┐  ┌───▼──┐  ┌───▼───┐
│ KPI │ │ Doc │  │  HR   │  │Proj │  │Alert │  │  NLP  │
│ Svc │ │ Svc │  │  Svc  │  │ Svc │  │ Svc  │  │  Svc  │
└──┬──┘ └──┬──┘  └───┬───┘  └──┬──┘  └───┬──┘  └───┬───┘
   │        │         │          │         │          │
┌──▼────────▼─────────▼──────────▼─────────▼──────────▼──────────┐
│                      Shared Data Layer                          │
│  PostgreSQL (multi-schema tenancy)  ·  Redis (cache/queue)     │
│  Garage / S3 (document store)  ·  TimescaleDB (KPI time-series)│
│  Elasticsearch (full-text + NLP index)                         │
└─────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      AI / ML Layer                              │
│  OCR (Tesseract + LLM post-correction)                         │
│  KPI Computation Engine (Python)                               │
│  Anomaly Detection (Isolation Forest / Z-score)                │
│  Ranking Predictor (weighted scoring model)                    │
│  NLP Assistant (LLM API + RAG over document index)             │
│  Professor Matching (embedding similarity + rule engine)       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Layer              | Technology                                            | Rationale                                             |
| ------------------ | ----------------------------------------------------- | ----------------------------------------------------- |
| Frontend           | React 18 + TypeScript + Recharts / D3                 | Component ecosystem; i18n RTL support                 |
| Mobile             | React Native                                          | Code-share with web; iOS + Android                    |
| API                | FastAPI (Python)                                      | Async, auto-OpenAPI, AI-native ecosystem              |
| Background Jobs    | Celery + Redis                                        | Scheduled ingestion, report generation                |
| Primary DB         | PostgreSQL 16 (schema-per-tenant)                     | ACID, row-level security, proven multi-tenancy        |
| Time-series        | TimescaleDB extension                                 | KPI trend queries; hypertable partitioning            |
| Document Store     | Garage (S3-compatible)                                | Self-hosted, no vendor lock; presigned URLs           |
| Search / NLP index | Elasticsearch 8                                       | Full-text over extracted docs; vector search          |
| Cache              | Redis 7                                               | KPI cache, session, pub/sub for alerts                |
| AI OCR             | Tesseract 5 + GPT-4o vision for correction            | Cost-effective; LLM handles ambiguous scans           |
| NLP / Chat         | Claude API (claude-sonnet-4-20250514) + LangChain RAG | Bilingual; document-grounded answers                  |
| ML Models          | scikit-learn / PyTorch + SHAP                         | Anomaly detection, explainability |
| Auth               | JWT + OAuth2 (Keycloak)                               | SSO-ready; Ministry LDAP integration path             |
| Infrastructure     | Docker + Kubernetes + Terraform                       | 35-tenant scale; horizontal pod autoscaling           |
| CI/CD              | GitHub Actions                                        | Automated test → build → deploy                       |
| Observability      | Prometheus + Grafana + Sentry                         | Metrics, dashboards, error tracking                   |

### 2.3 Multi-Tenancy Model

Each institution is a **tenant** — separate PostgreSQL schema (`tenant_{code}`), JWT-injected `tenant_id` on every query, Garage bucket per institution. Cross-tenant reads require `GLOBAL_READ` permission. All writes are logged to an immutable `audit_log` table (`action`, `user_id`, `tenant_id`, `old_value`, `new_value`, `created_at`).

---

## 3. Service Map

| Service           | Responsibilities                                                | Key Dependencies                                | Spec Document              |
| ----------------- | --------------------------------------------------------------- | ----------------------------------------------- | -------------------------- |
| `kpi-service`     | KPI computation, ranking, score aggregation, trend storage      | PostgreSQL, TimescaleDB, Redis                  | `specs/kpi-service.md`     |
| `doc-service`     | File upload, OCR, extraction, classification, template matching | Garage, Elasticsearch, OCR engine               | `specs/doc-service.md`     |
| `hr-service`      | Professor profiles, workload, hiring workflows, matching        | PostgreSQL, `kpi-service`                       | `specs/hr-service.md`      |
| `project-service` | Project posting, KPI-based matching, assignment tracking        | PostgreSQL, `kpi-service`, `hr-service`         | `specs/project-service.md` |
| `alert-service`   | Threshold monitoring, anomaly detection, notification dispatch  | Redis pub/sub, `kpi-service`, email/SMS gateway | `specs/alert-service.md`   |
| `accreditation-service` | Framework compliance evaluation, indicator status computation, gap analysis | PostgreSQL, `kpi-service`, `doc-service` | `specs/accreditation-service.md` |
| `nlp-service`     | Natural language queries, document Q&A, report narration        | Elasticsearch, Claude API, `doc-service`        | `specs/nlp-service.md`     |
| `report-service`  | Scheduled report generation, PDF/Excel export, MESRS format     | `kpi-service`, `doc-service`, Celery            | `specs/report-service.md`  |
| `auth-service`    | JWT issuance, RBAC enforcement, tenant routing, audit log       | Keycloak, PostgreSQL                            | `specs/auth-service.md`    |
| `admin-service`   | Tenant provisioning, user management, threshold configuration   | All services                                    | `specs/admin-service.md`   |

---

## 4. Module 1 — KPI Engine & Ranking Dashboard

### 4.1 Rationale: KPI Framework Design

The KPI system is designed to simultaneously serve two masters:

1. **Internal governance**: KPIs that UCAR leadership needs to manage 35 institutions operationally (ISO 21001:2018 alignment, HR equity, financial health).
2. **Accreditation compliance signal**: KPIs that map to the measurable controls in QS, THE, ARWU, ISO 21001, and MESRS frameworks — feeding the accreditation engine with automatically evaluated evidence.

The following section defines the full KPI catalog with explicit ranking mappings and data sources.

### 4.2 KPI Catalog

Demo scope: KPIs that feed the three accreditation frameworks in scope — **ISO 9001**, **ISO 21001**, **UI GreenMetric**. Research, Employability, Internationalization, and Finance domains are deferred.

##### DOMAIN B — Academic Quality & Teaching
_ISO 21001: clause 8.2 (student performance), 8.3 (curriculum design), 9.1 (monitoring)_

| KPI ID   | Name                          | Formula / Source                                                        | Framework       | Frequency |
| -------- | ----------------------------- | ----------------------------------------------------------------------- | --------------- | --------- |
| `ACA-01` | Student-Faculty Ratio         | Total enrolled students ÷ FTE academic staff                            | ISO 21001 8.1   | Semester  |
| `ACA-02` | Success Rate                  | Students who passed all modules ÷ total enrolled (per cohort)           | ISO 21001 9.1   | Semester  |
| `ACA-03` | Dropout Rate                  | Students who withdrew without graduating ÷ cohort size                  | ISO 21001 9.1   | Semester  |
| `ACA-05` | Curriculum Coverage Rate      | Actual delivered hours ÷ minimum required hours per module (%)          | ISO 21001 8.3   | Semester  |
| `ACA-12` | Weak Student Remediation Rate | At-risk students receiving formal support ÷ identified at-risk students | ISO 21001 8.2   | Semester  |

---

##### DOMAIN G — Sustainability & ESG
_UI GreenMetric: Energy & Climate Change, Waste, Water, Transport, Education & Research, Setting & Infrastructure_

| KPI ID   | Name                           | Formula / Source                                            | GreenMetric Category          | Frequency |
| -------- | ------------------------------ | ----------------------------------------------------------- | ----------------------------- | --------- |
| `ESG-01` | Energy Consumption per Student | kWh consumed ÷ enrolled students                            | Energy & Climate Change       | Monthly   |
| `ESG-02` | Carbon Footprint per Student   | CO2e kg ÷ enrolled students                                 | Energy & Climate Change       | Annual    |
| `ESG-03` | Renewable Energy Rate          | Renewable energy consumed ÷ total energy consumed           | Energy & Climate Change       | Annual    |
| `ESG-04` | Recycling Rate                 | Waste recycled ÷ total waste generated                      | Waste                         | Annual    |
| `ESG-05` | Green Transportation Rate      | Students/staff using sustainable transport ÷ total (survey) | Transport                     | Annual    |
| `ESG-06` | Campus Accessibility Score     | Accessibility-compliant facilities ÷ total facilities       | Setting & Infrastructure      | Annual    |
| `ESG-07` | Gender Diversity Index         | Female faculty ÷ total faculty                              | Education & Research          | Annual    |
| `ESG-08` | SDG-Aligned Research Rate      | Publications linked to UN SDGs ÷ total publications         | Education & Research          | Annual    |

---

##### DOMAIN H — Governance & Compliance
_ISO 9001 + ISO 21001 alignment_

| KPI ID   | Name                                  | Formula / Source                                                      | Framework          | Frequency |
| -------- | ------------------------------------- | --------------------------------------------------------------------- | ------------------ | --------- |
| `GOV-01` | Document Control Compliance           | Controlled documents current ÷ total controlled documents             | ISO 9001 7.5       | Monthly   |
| `GOV-02` | Internal Audit NCR Closure Rate       | Closed non-conformances ÷ total NCRs raised (90-day window)           | ISO 9001 9.2       | Quarterly |
| `GOV-03` | Governance Meeting Frequency          | Actual BOS/DAB/PAC meetings ÷ required meetings (per charter)         | ISO 21001 9.3      | Semester  |
| `GOV-04` | Risk Register Currency                | Days since last risk register update (target: ≤ 30 days)             | ISO 9001 6.1       | Monthly   |
| `GOV-05` | Stakeholder Feedback Action Rate      | Feedback items with closed action ÷ total feedback received           | ISO 21001 9.1      | Semester  |
| `GOV-06` | Document Completeness Index           | Required institutional documents present and current ÷ total required | ISO 9001 7.5       | Monthly   |

---

##### DOMAIN F — Human Resources (ISO 21001-relevant subset)

| KPI ID  | Name                         | Formula / Source                                                    | Framework     | Frequency |
| ------- | ---------------------------- | ------------------------------------------------------------------- | ------------- | --------- |
| `HR-01` | Workload Compliance Rate     | Faculty within ±20% of contracted hours ÷ total faculty             | ISO 21001 7.1 | Monthly   |
| `HR-05` | Training Fulfillment Rate    | Training hours completed ÷ training hours required                  | ISO 21001 7.2 | Annual    |
| `HR-09` | Faculty Expertise Match Rate | Faculty whose specialization matches their assigned courses ÷ total | ISO 21001 7.2 | Semester  |

---

### 4.3 Accreditation Compliance Engine

The platform includes a compliance mapping layer modeled after enterprise accreditation tools (Vanta, Drata, Sprinto). Each of the five target frameworks — QS, THE, ARWU, ISO 21001, MESRS — is defined as a set of **Controls**. Each control is satisfied by **Tests**, which are automatically evaluated as evidence flows in: documents ingested through the platform, approved KPI records, and attestations submitted by staff.

The key mechanism: every **Document Template** in the system (e.g. "Grade Sheet", "Faculty Record", "Disaster Recovery Procedure") is linked to one or more framework controls. When an institution uploads a document matching that template and it is approved, that document is automatically registered as evidence for each linked control, advancing the institution's compliance progress in real time.

**Control statuses** (matching industry conventions): `PASSING` · `FAILING` · `NEEDS_EVIDENCE` · `NOT_APPLICABLE` (user-declared, with reason — e.g. institution did not participate in a survey cycle)

**Test types**: Automated (KPI computation result meets threshold) · Document upload (approved document of required template type on file) · Attestation (staff acknowledgment, logged and timestamped)

> Full implementation specification: see [`.claude/accreditation.md`](.claude/accreditation.md)

#### UCAR Network Ranking (internal)

Institutions are ranked 1–35 by their **internal UCAR Score** — a weighted composite of computed KPI values used for internal governance and resource allocation decisions. This is an operational governance tool distinct from external framework compliance status. Weights are stored in `ucar_global.kpi_weights`, version-controlled with effective dates, and adjustable by authorized administrators without code deployment.

```
UCAR_Score = Σ (normalized_kpi_score_i × weight_i)
normalized_score_i = (institution_value_i − min_network_i) / (max_network_i − min_network_i) × 100
```

---

### 4.4 Dashboard Specification

#### Views

**1. University President View** (cross-institution)

- Ranked leaderboard of all 35 institutions by internal UCAR Score
- Domain radar charts: each institution's 8-domain KPI profile
- UCAR network aggregate score vs. last period
- Top 5 anomalies (institutions with largest negative KPI deltas)
- **Accreditation Posture Panel**: for each active target framework, show network-level control coverage (N passing / M total) with a progress bar — clicking through opens the Accreditation Dashboard
- Drill-down: click any institution → Dean View

**2. Dean View** (single institution)

- Institution UCAR Score + rank (#N of 35) + delta
- KPI cards for each domain with traffic-light status (green/amber/red)
- Time-series chart per KPI (configurable period)
- Comparison panel: institution vs. UCAR median vs. UCAR best
- Alert feed (institution-specific)
- Missing document warnings (feeds from doc-service)
- **Accreditation tab**: per-framework control pass rate + top failing controls

**3. Accreditation Dashboard** (full view — see `.claude/accreditation.md` for complete spec)

- Framework tabs: QS | THE | ARWU | ISO 21001 | MESRS
- Per framework: progress ring (% controls passing), control list with status badges, evidence portfolio, gap analysis sorted by weight × distance to passing
- Evidence Portfolio: all documents on file that are linked to at least one control in this framework, with their template type, upload date, and approval status

**4. KPI Detail View**

- Full time-series for one KPI
- Data lineage: which documents contributed to this value
- Last computation timestamp + source institution data
- Which framework controls this KPI feeds, with their current pass/fail status

#### Technical requirements

- All charts use Recharts with server-side aggregated data (no raw data to client)
- KPI cards subscribe via WebSocket and update when a new `kpi_records` row is written for their KPI — they do not poll on a 5-minute timer. Annual KPIs display their last computed value with a "last updated" timestamp; they do not re-render until a new computation is triggered.
- All views must render on screens as small as 1024px wide
- Export to PDF and Excel available on every view (server-side rendered)

---

## 5. Module 2 — Document Ingestion & Migration Pipeline

### 5.1 Problem Statement

UCAR's KPIs cannot be computed without data. That data currently exists in:

- Scanned paper records (unclear quality)
- Excel/CSV files (inconsistent schemas across institutions)
- Word/PDF documents (syllabi, budgets, HR records, inventories)
- Images of forms and tables

The ingestion pipeline must convert all of these into structured records that feed the KPI engine — reliably, at scale, and with human-in-the-loop validation for low-confidence extractions.

### 5.2 Document Taxonomy

Documents are classified into a controlled taxonomy. Each class maps to: a processing strategy, a set of extractable fields, and one or more target KPIs.

```
document_class
├── academic/
│   ├── syllabus                → ACA-05, ACA-09
│   ├── grade_sheet             → ACA-02, ACA-03, ACA-04, ACA-10
│   ├── attendance_log          → ACA-11, HR-01
│   └── exam_report             → ACA-02, ACA-10
├── hr/
│   ├── faculty_record          → HR-01-09, RES-02-03, ACA-06
│   ├── payslip                 → FIN-07, HR-01
│   ├── training_record         → HR-05
│   └── hiring_dossier          → HR-07, HR-08
├── finance/
│   ├── budget_report           → FIN-01, FIN-02, FIN-03
│   ├── project_balance_sheet   → FIN-06, RES-05, RES-06
│   └── inventory_sheet         → FIN-05
├── research/
│   ├── publication_list        → RES-01-04, RES-09
│   ├── project_proposal        → RES-05, RES-10
│   └── phd_enrollment_list     → RES-07, RES-08
├── external_relations/
│   ├── convention              → INT-05, EMP-04, ACA-07
│   ├── mobility_report         → INT-03, INT-04
│   └── employer_survey         → EMP-01-03, EMP-07
├── governance/
│   ├── meeting_minutes         → GOV-03
│   ├── audit_report            → GOV-02
│   └── risk_register           → GOV-04
└── esg/
    ├── energy_report           → ESG-01, ESG-02, ESG-03
    └── sustainability_survey   → ESG-04, ESG-05, ESG-07
```

### 5.3 Ingestion Architecture

#### Stage 1: Upload & Classification

```
User uploads file (any format)
         │
         ▼
┌─────────────────────┐
│  Format Normalizer  │
│  PDF → image pages  │
│  DOCX → text + imgs │
│  XLSX → JSON tables │
│  JPEG/PNG → pass    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Auto-Classifier    │  ← LLM-based document classifier
│  Input: first 2     │    (filename + first 500 tokens)
│  pages + filename   │    Returns: document_class + confidence
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
confidence > 0.85  confidence < 0.85
    │             │
    ▼             ▼
Auto-classify  Human review queue
               (staff sees: "What type is this?")
```

#### Stage 2: Extraction

Extraction strategy varies by document class:

| Strategy                        | Used For                                             | Engine                             |
| ------------------------------- | ---------------------------------------------------- | ---------------------------------- |
| **Structured table extraction** | Grade sheets, budgets, inventories (Excel/clean PDF) | pandas / tabula-py                 |
| **OCR + structured extraction** | Scanned forms, printed tables                        | Tesseract 5 → LLM field extraction |
| **Free-text NLP extraction**    | Conventions, meeting minutes, project descriptions   | LLM with structured output schema  |
| **Form field extraction**       | PDF forms with defined fields                        | PyMuPDF form reader                |
| **Visual grounding**            | Complex scanned layouts, handwritten annotations     | GPT-4o vision → field JSON         |

**Visual grounding** is mandatory for any scan where Tesseract confidence < 0.7. The document image is sent to GPT-4o vision with a structured prompt that includes the expected field schema for the document class. This catches:

- Handwritten values in printed forms
- Tables with merged cells
- Arabic text in mixed-language documents
- Non-standard layouts from different institutions

#### Stage 3: Validation

Every extracted record passes through a validation layer before being stored:

```python
class ExtractionValidation:
    schema_check: bool          # Required fields present + correct types
    range_check: bool           # Numeric values within plausible range
    cross_document_check: bool  # Consistent with prior records for same entity
    duplicate_check: bool       # Not a duplicate of existing record
    confidence_score: float     # Aggregate confidence (0.0 – 1.0)
    flagged_fields: list[str]   # Fields below individual confidence threshold
```

Records with `confidence_score < 0.75` or any `flagged_fields` are routed to the **human review queue**. Staff see the original document alongside the extracted values and can correct/approve field by field.

#### Stage 4: Template-Based Mass Migration

For mass migration of legacy documents, the system supports **Document Templates**:

```
A Document Template defines:
  - template_id
  - document_class
  - expected_fields: [{field_name, type, required, extraction_hint}]
  - layout_hints: {has_header_row, table_columns, date_format}
  - tagging_rules: [{filename_pattern, institution_code, academic_year}]
```

**Migration workflow:**

1. Admin creates or selects a Template for each document type in the legacy corpus
2. Admin uploads a batch (zip or folder) of legacy documents
3. System applies `tagging_rules` to auto-assign `institution_code`, `academic_year`, `document_class` from filename patterns (e.g., `INSAT_grades_2023_S2_*.xlsx`)
4. Template's `expected_fields` guide the extractor (field names are injected into the LLM prompt as structural hints)
5. Batch results shown in a review grid: N documents processed, N auto-approved, N flagged for review
6. Flagged documents queued for human correction
7. On approval, records are committed and KPIs recomputed

#### Stage 5: Storage & Post-Approval Events

```
Each extracted record stored as:
  - Raw file → Garage bucket (immutable, versioned)
  - Extracted JSON → PostgreSQL table `documents.extracted_records`
  - Full text → Elasticsearch index `docs-{tenant}`
  - Extraction metadata → `documents.ingestion_log` (confidence, strategy, reviewer)
```

On document approval (status transitions to `approved`), `doc-service` publishes a Redis pub/sub event to channel `events.document.approved`:

```json
{
  "event": "document.approved",
  "tenant_id": "<uuid>",
  "document_id": "<uuid>",
  "template_id": "<uuid>",
  "document_class": "<string>",
  "approved_at": "<iso8601>"
}
```

Consumers:
- `kpi-service` — triggers KPI recomputation for all KPI IDs in `kpi_definitions.data_sources` that include this `document_class`
- `accreditation-service` — triggers control re-evaluation for all tests linked to this `template_id` via `template_test_links`

If a document is later **rejected** (status → `rejected`), the same pattern fires on channel `events.document.rejected` with the same payload. Both services deactivate linked records (KPI records marked `is_estimated = true`; evidence records marked `is_active = false`) and re-evaluate downstream status.

### 5.4 Anomaly Detection in Documents

After extraction, an anomaly detector flags records that are statistically implausible:

- Grade distributions that are perfectly uniform (likely template not filled)
- Budget lines with round numbers only (likely estimated, not actual)
- Faculty hours that match exactly the contractual minimum (possibly copied)
- Dates inconsistent with the academic year derived from the filename
- Duplicate records for the same entity in the same period

Flagged anomalies are routed to the **document anomaly queue**, distinct from the extraction review queue, and displayed in the Alerts module.

### 5.5 Implementation Notes for Claude Code

```
doc-service/
├── api/
│   ├── upload.py           # Multipart upload endpoint, format detection
│   ├── classify.py         # Auto-classification endpoint
│   ├── review.py           # Human review queue API
│   └── templates.py        # Template CRUD
├── pipeline/
│   ├── normalizer.py       # Format → normalized representation
│   ├── classifier.py       # LLM-based document classifier
│   ├── extractors/
│   │   ├── table.py        # tabula-py / openpyxl structured extraction
│   │   ├── ocr.py          # Tesseract + LLM post-correction
│   │   ├── nlp.py          # Free-text LLM extraction
│   │   └── vision.py       # GPT-4o vision extraction
│   ├── validator.py        # Schema + range + duplicate checks
│   └── anomaly.py          # Post-extraction anomaly detection
├── storage/
│   ├── s3_client.py        # Raw file storage (Garage)
│   ├── pg_client.py        # Extracted record persistence
│   └── es_client.py        # Full-text indexing
└── workers/
    ├── ingestion_worker.py # Celery worker: process upload queue
    └── migration_worker.py # Celery worker: batch migration jobs
```

Key LLM prompt patterns are externalized to `prompts/` directory and version-controlled separately from code. This allows prompt tuning without code redeployment.

---

## 6. Module 3 — Professor & Staff Management

### 6.1 Professor Profile Data Model

```sql
-- Core professor record (lives in hr schema)
CREATE TABLE professors (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id),
  national_id     VARCHAR(20) UNIQUE NOT NULL,
  first_name      VARCHAR(100) NOT NULL,
  last_name       VARCHAR(100) NOT NULL,
  first_name_ar   VARCHAR(100),
  last_name_ar    VARCHAR(100),
  email           VARCHAR(255) UNIQUE NOT NULL,
  phone           VARCHAR(30),
  gender          VARCHAR(10) CHECK (gender IN ('M', 'F', 'other', 'undisclosed')),  -- required for ESG-07
  contract_type   VARCHAR(20) NOT NULL CHECK (contract_type IN ('permanent', 'contractual')),
  rank            VARCHAR(50),       -- Maître assistant A/B, Maître de conférences, Professeur
  position_status VARCHAR(20),       -- active, on_leave, suspended, retired
  hire_date       DATE,
  min_hours       INTEGER,           -- contractual minimum teaching hours/semester
  max_hours       INTEGER,           -- overwork threshold
  base_salary     NUMERIC(12,3),
  photo_url       TEXT,
  h_index         INTEGER,           -- stored after Scopus sync or manual entry; used for RES-02
  h_index_updated_at TIMESTAMPTZ,   -- when h_index was last synced
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE professor_specializations (
  id              UUID PRIMARY KEY,
  professor_id    UUID REFERENCES professors(id),
  domain          VARCHAR(100) NOT NULL,
  subdomain       VARCHAR(100),
  level           VARCHAR(20) CHECK (level IN ('primary', 'secondary', 'emerging')),
  verified        BOOLEAN DEFAULT false
);

CREATE TABLE professor_degrees (
  id              UUID PRIMARY KEY,
  professor_id    UUID REFERENCES professors(id),
  degree_type     VARCHAR(50),       -- PhD, Habilitation, Licence, Master
  field           VARCHAR(200),
  institution     VARCHAR(200),
  country         VARCHAR(100),
  year            INTEGER,
  document_url    TEXT               -- link to uploaded diploma in Garage
);

CREATE TABLE professor_positions (
  id              UUID PRIMARY KEY,
  professor_id    UUID REFERENCES professors(id),
  institution_id  UUID,
  title           VARCHAR(200),
  department      VARCHAR(200),
  start_date      DATE,
  end_date        DATE,              -- NULL if current
  is_current      BOOLEAN DEFAULT false
);

CREATE TABLE professor_publications (
  id              UUID PRIMARY KEY,
  professor_id    UUID REFERENCES professors(id),
  title           TEXT NOT NULL,
  journal         VARCHAR(300),
  year            INTEGER,
  doi             VARCHAR(200),
  scopus_id       VARCHAR(100),
  citation_count  INTEGER DEFAULT 0,
  source          VARCHAR(30) CHECK (source IN ('manual', 'scopus_api', 'doc_extract'))
);

CREATE TABLE professor_hours (
  id              UUID PRIMARY KEY,
  professor_id    UUID REFERENCES professors(id),
  semester        VARCHAR(10),       -- e.g. 2025-S1
  course_code     VARCHAR(50),
  course_name     VARCHAR(300),
  hours_scheduled INTEGER,
  hours_delivered INTEGER,
  hours_extra     INTEGER GENERATED ALWAYS AS (GREATEST(hours_delivered - hours_scheduled, 0)) STORED
);
```

### 6.2 Professor Dashboard (Individual View)

Each professor has a profile card accessible to the HR Manager and Dean:

**Displayed fields:**

- Name (fr + ar), photo, rank, contract type, current institution
- Specializations (primary + secondary, verified badge)
- H-index (from Scopus API or manual entry), citation count
- Degrees timeline
- Current position + position history
- Teaching workload: scheduled hours vs. delivered vs. contractual minimum
  - Visual: gauge chart (green = within range, red = over/under)
  - Overwork hours highlighted + estimated overwork pay
- Publications list with citation counts, filterable by year
- KPI contribution score: how this professor's data affects institution KPIs
- Documents on file: diplomas, contracts, payslips (with upload shortcut)

### 6.3 Professor Matching Engine

#### Use case 1: Module-to-Professor matching

When an institution needs to assign a professor to a course module, the system suggests ranked candidates:

```
Input:
  course_specialization (e.g., "Machine Learning")
  institution_id
  semester
  required_hours

Matching algorithm:
  1. Filter: active professors with at least one specialization matching course domain
     (semantic similarity using sentence embeddings, threshold 0.75)
  2. Filter: professors with available capacity
     (current scheduled hours + required_hours ≤ max_hours)
  3. Score each candidate:
     match_score = (0.4 × specialization_similarity)
                 + (0.2 × h_index_normalized)
                 + (0.2 × available_capacity_score)
                 + (0.1 × student_feedback_score)
                 + (0.1 × same_institution_priority)
  4. Return ranked list with score breakdown
```


---

## 7. Module 4 — Project Matching Dashboard

### 7.1 Concept

Research and industry projects are matched to institutions based on institutional KPI profiles, available expertise, and historical project performance — not arbitrary assignment or personal relationships.

### 7.2 Project Types

| Type                          | Posted By                  | Matched To                     | Criteria                                      |
| ----------------------------- | -------------------------- | ------------------------------ | --------------------------------------------- |
| Research project              | UCAR / Ministry / Industry | Institution + specific faculty | Research KPIs (RES-01-11), faculty expertise  |
| Industry collaboration        | Company (via portal)       | Institution + faculty          | EMP-04, faculty industry experience           |
| Student mobility / Erasmus    | Foreign partner            | Institution                    | INT-01-04, ACA-07, language programs          |
| Funded infrastructure project | Ministry                   | Institution                    | Infrastructure needs score, FIN-01 compliance |
| Accreditation audit support   | UCAR central               | Institution                    | GOV-01-06 scores, ISO compliance              |

### 7.3 Matching Algorithm

```
Input: Project requirements
  - required_specializations: [list]
  - required_kpi_thresholds: {kpi_id: min_value}
  - budget_range: [min, max]
  - duration_months: int
  - prerequisites: [past_project_type]

Matching steps:
  1. Hard filter: institutions meeting all required_kpi_thresholds
  2. Soft score each passing institution:
       project_fit_score = (0.35 × specialization_match_score)
                         + (0.25 × relevant_kpi_score_normalized)
                         + (0.20 × past_project_success_rate)
                         + (0.10 × available_capacity_score)
                         + (0.10 × geographic_fit_score)
  3. Within matched institution, rank individual faculty by professor matching score
  4. Return: top 3 institution matches with score breakdown + recommended lead faculty
```

### 7.4 Project Dashboard View

- **Project board**: Kanban — Open / Matched / Active / Completed
- **Post project**: Form → auto-generates matching results on submit
- **Match report**: Institution score breakdown + "why this institution" SHAP explanation
- **Assignment tracking**: Milestones, deliverables, budget burn, KPI impact forecast
- **Historical performance**: Institution's past project completion rate, budget compliance

---

## 8. Module 5 — Alerts & Compliance Engine

### 8.1 Alert Types

| Alert Level  | Trigger                                                                         | Response Time        | Channel              |
| ------------ | ------------------------------------------------------------------------------- | -------------------- | -------------------- |
| `INFO`       | KPI moves into amber zone                                                       | Next dashboard visit | In-app only          |
| `WARNING`    | KPI crosses warning threshold or missing document due in 7 days                 | < 1 hour             | In-app + email       |
| `CRITICAL`   | KPI crosses critical threshold, missing required document, compliance violation | < 5 minutes          | In-app + email + SMS |
| `PREDICTIVE` | ML model forecasts threshold breach within 30 days                              | Daily batch          | In-app + email       |

### 8.2 Alert Catalog

**Academic**

- Dropout rate > 15% → WARNING; > 25% → CRITICAL
- Curriculum coverage < 80% → WARNING; < 60% → CRITICAL
- Student-faculty ratio > 25 → WARNING; > 35 → CRITICAL

**Finance**

- Budget execution > 90% before end of fiscal period → WARNING; > 98% → CRITICAL
- Project budget overrun > 10% → WARNING; > 25% → CRITICAL

**HR**

- Professor with hours deficit > 20% → WARNING
- Professor with hours overrun > 50% → CRITICAL (labor law risk)
- Unfilled position > 45 days → WARNING; > 90 days → CRITICAL

**Documents**

- Required annual document not uploaded by deadline → WARNING (7 days before); CRITICAL (overdue)
- Document extraction confidence < 0.5 on required field → WARNING
- Document anomaly detected → WARNING

**Compliance / ISO 21001**

- NCR open > 60 days → WARNING; > 90 days → CRITICAL
- Risk register not updated > 30 days → WARNING
- Governance meeting missed → WARNING

**Predictive**

- Dropout risk model: cohort predicted to exceed threshold in next semester → PREDICTIVE
- Budget overrun model: trajectory exceeds allocation → PREDICTIVE
- KPI regression: institution score declining for 3 consecutive periods → PREDICTIVE

### 8.3 Alert Engine Architecture

```
KPI Batch Completion Event
         │
         ▼
┌────────────────────┐
│  Threshold Checker │ ← reads kpi_thresholds table
│  (runs on each     │    per-institution, per-KPI
│  KPI update)       │    configurable by Dean/Admin
└────────┬───────────┘
         │
    ┌────┴────┐
    │         │
 threshold   ML anomaly
 crossed?    detected?
    │         │
    ▼         ▼
┌─────────────────────┐
│   Alert Factory     │
│   Creates alert     │
│   record + payload  │
│   Determines level  │
│   Adds explanation  │
│   + recommended CTA │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Notification       │
│  Dispatcher         │
│  Routes by role +   │
│  alert level +      │
│  institution        │
└──┬──────────────────┘
   │
   ├── In-app (WebSocket push → Redis pub/sub)
   ├── Email (SendGrid / SMTP)
   └── SMS (Twilio) ← CRITICAL only
```

### 8.4 Mini Audit Report Generation

When a CRITICAL alert fires (or on demand by Dean/President), the system generates a **Mini Audit Report**:

```
Mini Audit Report contains:
  - Institution name + period
  - Triggered alert(s) with description and data evidence
  - Historical trend chart for affected KPI(s) (3 periods)
  - Comparative context: how institution compares to UCAR network
  - Root cause hypotheses (NLP-generated from document analysis)
  - Recommended corrective actions (templated + AI-generated)
  - Required documents to resolve issue (if applicable)
  - Deadline for response (configurable, default 30 days)
  - Signature block for Dean acknowledgment
```

Format: PDF (auto-generated, stored in doc-service, sent by email).

---

## 9. Module 6 — Student Management & Teacher Assignment

> **Demo scope**: frontend only — no backend API for this module yet. Mock data drives all views.

### 9.1 Purpose

Centralise academic organisation: students, classes, teacher assignments, and schedules in one place. Currently managed per-institution in disparate Excel files. This module gives deans and administrative staff a live view of institutional structure and feeds KPIs ACA-01 through ACA-05, HR-01, HR-09.

### 9.2 Core Entities

**Student**
- Personal info: national ID, full name (fr + ar), DOB, gender, nationality
- Academic info: program, cohort year, current level (L1/L2/L3/M1/M2/Doctorat)
- Status: `enrolled` | `on_leave` | `graduated` | `withdrawn`
- Linked grades, attendance records, and enrolled classes

**Class (Section)**
- Class code, name, program, academic year, semester
- Enrolled students list
- Assigned teacher + co-teacher (optional)
- Schedule: day/time/room slots
- Syllabus reference (links to a doc-service `syllabus` document)
- Delivered hours vs. required hours (feeds ACA-05)

**Program**
- Code, name, level (Licence/Master/Doctorat/Ingénieur), department
- Required modules list per semester
- Total credit hours

**Schedule Slot**
- Class + day_of_week + start_time + end_time + room + recurrence
- Conflict detection: same teacher or same room at overlapping times

### 9.3 Teacher Assignment

Assignment is the act of attaching a professor to a class for a semester. It is separate from the professor's general profile (Module 3) — one professor can be assigned to multiple classes.

```
Assignment
  professor_id    → links to hr-service professor record
  class_id
  semester        e.g. "2025-S1"
  role            LEAD | SUPPORT | EVALUATOR
  scheduled_hours auto-summed from Schedule Slots for this class
  delivered_hours updated as semester progresses (from attendance logs)
```

**Assignment Rules (enforced on save):**
- Professor must have a specialization matching the class subject (semantic match, HR-09)
- Professor's total scheduled hours for semester must not exceed `max_hours` (HR-01 compliance)
- No two assignments can create a schedule conflict for the same professor
- Warning (not block) if assigning a contractual professor to a core required module

**Assignment Suggestions**: When creating a new class assignment, the system calls the existing professor matching engine (§6.3 Use case 1) and pre-populates a ranked candidate list.

### 9.4 Dashboard Views (Frontend Demo)

**1. Program Structure View** (Dean)
- Tree: Program → Semesters → Modules → Classes
- Each class card shows: assigned teacher (or "Unassigned" in red), enrolled count, delivered/required hours progress bar
- One-click "Assign teacher" → opens matching suggestions panel

**2. Student List View** (Admin Staff)
- Filterable table: program, cohort, level, status
- Bulk actions: import from CSV, export, change status
- Click student → Student Profile (grades timeline, enrolled classes, attendance rate, at-risk flag)

**3. Class Detail View** (Dean / Admin)
- Header: class code, program, semester, teacher chip
- Tabs: Students (roster) | Schedule (weekly calendar) | Grades (grade distribution histogram) | Attendance (heatmap)
- Inline grade entry for evaluators

**4. Teacher Workload View** (HR Manager)
- One row per professor: name, contracted hours, scheduled hours, delivered hours, compliance gauge (HR-01)
- Colour coding: green (within range) · amber (approaching limit) · red (over max or under min)
- Click row → professor's class list for semester

**5. Schedule Builder** (Admin)
- Drag-and-drop weekly calendar grid
- Conflict highlighting: red overlay when a slot conflicts with existing assignment
- Room utilisation sidebar

### 9.5 Data Model

```sql
CREATE TABLE students (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id),
  national_id     VARCHAR(20) UNIQUE NOT NULL,
  first_name      VARCHAR(100) NOT NULL,
  last_name       VARCHAR(100) NOT NULL,
  first_name_ar   VARCHAR(100),
  last_name_ar    VARCHAR(100),
  dob             DATE,
  gender          VARCHAR(10),
  nationality     VARCHAR(3) DEFAULT 'TN',
  program_id      UUID REFERENCES programs(id),
  cohort_year     INTEGER,
  current_level   VARCHAR(20),
  status          VARCHAR(20) CHECK (status IN ('enrolled','on_leave','graduated','withdrawn'))
);

CREATE TABLE programs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id),
  code            VARCHAR(30) UNIQUE NOT NULL,
  name_fr         VARCHAR(300) NOT NULL,
  name_ar         VARCHAR(300),
  level           VARCHAR(20) CHECK (level IN ('Licence','Master','Ingenieur','Doctorat')),
  department      VARCHAR(200),
  total_credits   INTEGER
);

CREATE TABLE classes (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id),
  code            VARCHAR(30) NOT NULL,
  name_fr         VARCHAR(300) NOT NULL,
  program_id      UUID REFERENCES programs(id),
  academic_year   VARCHAR(10),
  semester        VARCHAR(10),
  required_hours  INTEGER,
  delivered_hours INTEGER DEFAULT 0,
  syllabus_doc_id UUID               -- FK to documents.files
);

CREATE TABLE class_enrollments (
  class_id    UUID REFERENCES classes(id),
  student_id  UUID REFERENCES students(id),
  enrolled_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (class_id, student_id)
);

CREATE TABLE teacher_assignments (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  class_id        UUID NOT NULL REFERENCES classes(id),
  professor_id    UUID NOT NULL,     -- FK to hr-service professors
  semester        VARCHAR(10) NOT NULL,
  role            VARCHAR(20) CHECK (role IN ('LEAD','SUPPORT','EVALUATOR')),
  scheduled_hours INTEGER,
  delivered_hours INTEGER DEFAULT 0,
  UNIQUE (class_id, professor_id, semester)
);

CREATE TABLE schedule_slots (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  class_id        UUID NOT NULL REFERENCES classes(id),
  day_of_week     INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
  start_time      TIME NOT NULL,
  end_time        TIME NOT NULL,
  room            VARCHAR(100),
  recurrence      VARCHAR(20) DEFAULT 'WEEKLY'
);

CREATE TABLE student_grades (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id      UUID NOT NULL REFERENCES students(id),
  class_id        UUID NOT NULL REFERENCES classes(id),
  assessment_type VARCHAR(30),   -- EXAM, CC, TP, PROJECT
  score           NUMERIC(5,2),
  max_score       NUMERIC(5,2) DEFAULT 20,
  graded_at       TIMESTAMPTZ
);
```

### 9.6 KPI Feed

| KPI | Source |
|-----|--------|
| `ACA-01` Student-Faculty Ratio | `COUNT(students WHERE status=enrolled)` ÷ FTE professors |
| `ACA-02` Success Rate | Students with mean grade ≥ 10 ÷ cohort |
| `ACA-03` Dropout Rate | Students with status=withdrawn ÷ cohort |
| `ACA-05` Curriculum Coverage | `SUM(delivered_hours)` ÷ `SUM(required_hours)` per class |
| `HR-01` Workload Compliance | `teacher_assignments.delivered_hours` vs `professors.min/max_hours` |
| `HR-09` Expertise Match | Matched assignments ÷ total assignments |

---

## 10. Data Models

### 10.0 Accreditation Tables

Core entities: `frameworks`, `framework_controls`, `control_tests` (automated / document-upload / attestation), `control_evidence` (links approved documents and KPI records to tests), `control_status` (live pass/fail per institution per control). Document templates carry `linked_test_ids[]` so that any approved document of that template type auto-satisfies the mapped tests.

Full schema: see `.claude/accreditation.md`.

### 10.1 Core Tables (Shared Schema: `ucar_global`)

```sql
-- Tenants (institutions)
CREATE TABLE tenants (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code            VARCHAR(20) UNIQUE NOT NULL,  -- e.g. 'INSAT', 'IHEC'
  name_fr         VARCHAR(300) NOT NULL,
  name_ar         VARCHAR(300),
  institution_type VARCHAR(50),   -- faculty, engineering_school, higher_institute, etc.
  city            VARCHAR(100),
  founded_year    INTEGER,
  is_active       BOOLEAN DEFAULT true,
  config          JSONB DEFAULT '{}'  -- tenant-specific settings
);

-- KPI definitions (what KPIs exist and how they're weighted)
CREATE TABLE kpi_definitions (
  id              UUID PRIMARY KEY,
  kpi_id          VARCHAR(10) UNIQUE NOT NULL,  -- e.g. 'RES-01'
  name_fr         VARCHAR(300) NOT NULL,
  name_ar         VARCHAR(300),
  domain          VARCHAR(20) NOT NULL,  -- RESEARCH, ACADEMIC, EMPLOYMENT, etc.
  formula_desc    TEXT,
  data_sources    TEXT[],   -- document classes that feed this KPI
  ranking_signal  JSONB,    -- {qs: 0.20, the: 0.30, arwu: 0.0}
  ucar_weight     NUMERIC(5,4),  -- weight in UCAR composite score
  computation_freq VARCHAR(20),  -- MONTHLY, SEMESTER, ANNUAL
  is_ranking_aligned BOOLEAN DEFAULT false
);

-- KPI weight versions (audit trail for weight changes)
CREATE TABLE kpi_weight_versions (
  id              UUID PRIMARY KEY,
  kpi_id          VARCHAR(10) REFERENCES kpi_definitions(kpi_id),
  weight          NUMERIC(5,4),
  effective_from  DATE,
  effective_to    DATE,
  changed_by      UUID,
  change_reason   TEXT
);

-- KPI records (computed values per institution per period)
-- Converted to TimescaleDB hypertable on computed_at after creation:
--   SELECT create_hypertable('kpi_records', 'computed_at', chunk_time_interval => INTERVAL '3 months');
CREATE TABLE kpi_records (
  id              UUID NOT NULL,
  tenant_id       UUID REFERENCES tenants(id),
  kpi_id          VARCHAR(10) REFERENCES kpi_definitions(kpi_id),
  value           NUMERIC(15,4),
  normalized_score NUMERIC(5,2),   -- 0-100
  period_start    DATE,
  period_end      DATE,
  computed_at     TIMESTAMPTZ NOT NULL,  -- hypertable partition key
  source_doc_ids  UUID[],          -- traceability: which documents were inputs
  source_field_refs JSONB,         -- {doc_id: [field_names_used]} — granular lineage
  computation_log JSONB,           -- intermediate values for audit (required, not nullable)
  is_estimated    BOOLEAN DEFAULT false,  -- true if imputed from incomplete data
  PRIMARY KEY (id, computed_at)
);

-- UCAR Composite Scores
CREATE TABLE institution_scores (
  id              UUID PRIMARY KEY,
  tenant_id       UUID REFERENCES tenants(id),
  period_start    DATE,
  period_end      DATE,
  composite_score NUMERIC(5,2),   -- 0-100
  rank            INTEGER,
  rank_delta      INTEGER,         -- vs previous period
  domain_scores   JSONB,          -- {RESEARCH: 72.3, ACADEMIC: 68.1, ...}
  computed_at     TIMESTAMPTZ
);

-- Alerts
CREATE TABLE alerts (
  id              UUID PRIMARY KEY,
  tenant_id       UUID REFERENCES tenants(id),
  kpi_id          VARCHAR(10),
  alert_type      VARCHAR(20) CHECK (alert_type IN ('THRESHOLD', 'ANOMALY', 'DOCUMENT', 'PREDICTIVE', 'COMPLIANCE')),
  level           VARCHAR(10) CHECK (level IN ('INFO', 'WARNING', 'CRITICAL', 'PREDICTIVE')),
  title_fr        TEXT,
  title_ar        TEXT,
  message_fr      TEXT,
  message_ar      TEXT,
  explanation     TEXT,
  recommended_action TEXT,
  evidence        JSONB,           -- {kpi_value, threshold, trend_data}
  is_resolved     BOOLEAN DEFAULT false,
  resolved_at     TIMESTAMPTZ,
  resolved_by     UUID,
  resolution_notes TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 10.2 Document Tables (`documents` schema)

```sql
CREATE TABLE documents.files (
  id              UUID PRIMARY KEY,
  tenant_id       UUID REFERENCES ucar_global.tenants(id),
  original_name   TEXT NOT NULL,
  storage_path    TEXT NOT NULL,   -- S3 key in Garage bucket
  mime_type       VARCHAR(100),
  file_size_bytes BIGINT,
  document_class  VARCHAR(50),
  template_id     UUID,
  academic_year   VARCHAR(10),
  status          VARCHAR(20) CHECK (status IN ('pending', 'processing', 'extracted', 'review', 'approved', 'rejected')),
  uploaded_by     UUID,
  uploaded_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents.extraction_results (
  id              UUID PRIMARY KEY,
  file_id         UUID REFERENCES documents.files(id),
  extracted_fields JSONB NOT NULL,
  confidence_scores JSONB,         -- per-field confidence
  overall_confidence NUMERIC(4,3),
  strategy_used   VARCHAR(30),     -- table|ocr|nlp|vision|form
  flagged_fields  TEXT[],
  anomalies       JSONB,
  reviewed_by     UUID,
  review_notes    TEXT,
  approved_at     TIMESTAMPTZ
);

CREATE TABLE documents.templates (
  id              UUID PRIMARY KEY,
  name            VARCHAR(200) NOT NULL,
  document_class  VARCHAR(50) NOT NULL,
  expected_fields JSONB NOT NULL,
  layout_hints    JSONB,
  tagging_rules   JSONB,
  created_by      UUID,
  is_active       BOOLEAN DEFAULT true
);
```

---

## 11. API Contract — Demo Scope

REST. Base: `https://api.ucar-erp.tn/v1/`. Auth: `Authorization: Bearer {jwt}`. Tenant injected from JWT; cross-tenant requires `GLOBAL_READ`.

```
/auth/    POST login · POST refresh · GET me
/kpi/     GET records?period=&domain= · GET scores/institution · GET scores/network · POST recompute
/documents/ POST upload · GET review/queue · POST review/{id}/approve · POST review/{id}/reject · GET templates/
/hr/      GET professors/ · POST professors/ · GET professors/{id} · PUT professors/{id} · GET professors/{id}/hours · GET professors/match
/students/ GET · POST · GET {id} · PUT {id} · GET {id}/enrollments · GET {id}/grades
/classes/  GET · POST · GET {id} · PUT {id} · POST {id}/assign-teacher · GET {id}/students · GET {id}/schedule
/alerts/  GET · POST {id}/resolve · GET thresholds/ · PUT thresholds/{kpi_id}
/accreditation/ GET frameworks/ · GET frameworks/{code}/status · GET frameworks/{code}/evidence · GET frameworks/{code}/gaps · POST controls/{id}/attest · POST controls/{id}/not-applicable
```

Error format: `{ "error": { "code": "...", "message_fr": "...", "detail": "...", "tenant_id": "uuid" } }`

---

## 12. Security Principles

- PostgreSQL RLS on every tenant-scoped table: `tenant_id = current_setting('app.current_tenant')::uuid`
- JWT claims set `app.current_tenant` at session start
- Audit log on all writes: `action`, `user_id`, `tenant_id`, `entity_type`, `entity_id`, `old_value`, `new_value`, `ip_address`, `created_at`
- Garage pre-signed URLs scoped per tenant, expire in 15 minutes

---

## 13. Deployment

Docker Compose (local): `api-gateway` · `kpi-service` · `doc-service` · `hr-service` · `student-service` · `alert-service` · `accreditation-service` · `auth-service` · `worker` · `beat` · `postgres` · `redis` · `garage` · `elasticsearch` · `frontend`

---

_End of UCAR ERP Master Document — Demo Scope_
