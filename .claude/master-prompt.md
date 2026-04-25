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
| University President | KPI Dashboard, Alerts          | Consolidated cross-institution view, ranking prediction |
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
│  MinIO / S3 (document store)  ·  TimescaleDB (KPI time-series) │
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
| Document Store     | MinIO (S3-compatible)                                 | Self-hosted, no vendor lock; presigned URLs           |
| Search / NLP index | Elasticsearch 8                                       | Full-text over extracted docs; vector search          |
| Cache              | Redis 7                                               | KPI cache, session, pub/sub for alerts                |
| AI OCR             | Tesseract 5 + GPT-4o vision for correction            | Cost-effective; LLM handles ambiguous scans           |
| NLP / Chat         | Claude API (claude-sonnet-4-20250514) + LangChain RAG | Bilingual; document-grounded answers                  |
| ML Models          | scikit-learn / PyTorch + SHAP                         | Anomaly detection, ranking prediction, explainability |
| Auth               | JWT + OAuth2 (Keycloak)                               | SSO-ready; Ministry LDAP integration path             |
| Infrastructure     | Docker + Kubernetes + Terraform                       | 35-tenant scale; horizontal pod autoscaling           |
| CI/CD              | GitHub Actions                                        | Automated test → build → deploy                       |
| Observability      | Prometheus + Grafana + Sentry                         | Metrics, dashboards, error tracking                   |

### 2.3 Multi-Tenancy Model

Each institution is a **tenant**. Tenancy is enforced at three levels:

1. **Database**: Separate PostgreSQL schema per tenant (`tenant_{institution_code}`). Shared schema for UCAR-level aggregates (`ucar_global`).
2. **Application**: Every API handler extracts `tenant_id` from the authenticated JWT and injects it into all queries. No cross-tenant query is possible without the `GLOBAL_READ` permission.
3. **Storage**: MinIO bucket per tenant (`docs-{institution_code}`). Pre-signed URLs are scoped and expire after 15 minutes.

---

## 3. Service Map

| Service           | Responsibilities                                                | Key Dependencies                                | Spec Document              |
| ----------------- | --------------------------------------------------------------- | ----------------------------------------------- | -------------------------- |
| `kpi-service`     | KPI computation, ranking, score aggregation, trend storage      | PostgreSQL, TimescaleDB, Redis                  | `specs/kpi-service.md`     |
| `doc-service`     | File upload, OCR, extraction, classification, template matching | MinIO, Elasticsearch, OCR engine                | `specs/doc-service.md`     |
| `hr-service`      | Professor profiles, workload, hiring workflows, matching        | PostgreSQL, `kpi-service`                       | `specs/hr-service.md`      |
| `project-service` | Project posting, KPI-based matching, assignment tracking        | PostgreSQL, `kpi-service`, `hr-service`         | `specs/project-service.md` |
| `alert-service`   | Threshold monitoring, anomaly detection, notification dispatch  | Redis pub/sub, `kpi-service`, email/SMS gateway | `specs/alert-service.md`   |
| `nlp-service`     | Natural language queries, document Q&A, report narration        | Elasticsearch, Claude API, `doc-service`        | `specs/nlp-service.md`     |
| `report-service`  | Scheduled report generation, PDF/Excel export, MESRS format     | `kpi-service`, `doc-service`, Celery            | `specs/report-service.md`  |
| `auth-service`    | JWT issuance, RBAC enforcement, tenant routing, audit log       | Keycloak, PostgreSQL                            | `specs/auth-service.md`    |
| `admin-service`   | Tenant provisioning, user management, threshold configuration   | All services                                    | `specs/admin-service.md`   |

---

## 4. Module 1 — KPI Engine & Ranking Dashboard

### 4.1 Rationale: KPI Framework Design

The KPI system is designed to simultaneously serve two masters:

1. **Internal governance**: KPIs that UCAR leadership needs to manage 35 institutions operationally (ISO 21001:2018 alignment, HR equity, financial health).
2. **International ranking signal**: KPIs that directly or proximally map to QS, THE, and Shanghai/ARWU ranking methodologies — the only way to predict and improve UCAR's global standing.

The following section defines the full KPI catalog with explicit ranking mappings and data sources.

### 4.2 KPI Catalog — Filtered & Enriched

#### Filtering rationale applied to your draft

The following proposed metrics were **removed** from the ranking-aligned set because they do not appear in any of QS (9 indicators), THE (13 indicators), or ARWU (6 indicators) methodologies and have no proxy relationship to them:

- LinkedIn scraping for employment rate → replaced by formal survey-based Employability Index (QS Employment Outcomes, 5%)
- ISO 21001 governance checkbox → retained as **internal compliance KPI only**, not ranking-contributing
- Club activities / extracurricular → retained as **internal student life KPI**, not ranking-contributing
- PFE / internship counts (alone) → absorbed into Employer Reputation proxy score
- Lesson plan completion rate → internal quality KPI, no ranking proxy
- Equipment maintenance compliance → internal operations KPI, no ranking proxy

The following metrics were **added** based on ranking gap analysis:

- H-index per faculty (QS Citations per Faculty, 20%)
- International faculty ratio (QS, 5%)
- International student ratio (QS, 5%)
- International Research Network score — co-authorship breadth (QS, 5%)
- Doctorates-awarded-to-academic-staff ratio (THE Teaching, 6%)
- Institutional research income (THE Research, 6%)
- Nobel/Fields Medal affiliations (ARWU, 30%) — tracked as binary, expected zero for UCAR; included for completeness
- Sustainability score composite (QS, 5%; THE, 7.5%)

---

#### KPI Catalog — Full Definition

Each KPI entry specifies: ID, name, domain, formula or data source, ranking signal (QS / THE / ARWU), internal weight, computation frequency, and data owner.

---

##### DOMAIN A — Research & Citations

_QS weight: Citations per Faculty 20% + International Research Network 5% | THE: Research 30% + Citations 30% | ARWU: Publications 20% + HiCi 20%_

| KPI ID   | Name                                 | Formula / Source                                                          | Ranking Signal               | Frequency |
| -------- | ------------------------------------ | ------------------------------------------------------------------------- | ---------------------------- | --------- |
| `RES-01` | Citations per Faculty                | Total Scopus/WoS citations (5yr) ÷ number of full-time equivalent faculty | **QS 20% · THE 30%**         | Annual    |
| `RES-02` | H-index (faculty median)             | Median h-index of all active faculty (Scopus)                             | QS proxy · THE proxy         | Annual    |
| `RES-03` | Publications per Faculty             | Peer-reviewed publications (5yr) ÷ FTE faculty                            | THE Research 6%              | Annual    |
| `RES-04` | International Research Network Score | % of publications with at least one international co-author               | **QS 5%**                    | Annual    |
| `RES-05` | Funded R&D Projects                  | Count of externally funded research projects (active)                     | THE Research income 6%       | Semester  |
| `RES-06` | Research Income per Faculty          | Total external research funding (TND) ÷ FTE faculty                       | THE Research income 6%       | Annual    |
| `RES-07` | PhD Students per Faculty             | Active doctoral students ÷ FTE faculty                                    | THE Teaching (DoctoralRatio) | Semester  |
| `RES-08` | Doctorates Awarded Ratio             | Doctorates awarded per year ÷ FTE academic staff                          | **THE Teaching 6%**          | Annual    |
| `RES-09` | High-Citation Papers (top 1%)        | Count of papers in top 1% by citations in their field (Scopus)            | THE Citations 30%            | Annual    |
| `RES-10` | Consultancy Revenue                  | Revenue from consultancy and knowledge transfer (TND)                     | THE Research income          | Annual    |
| `RES-11` | Open Access Publication Rate         | % of publications available open access                                   | Sustainability proxy         | Annual    |

---

##### DOMAIN B — Academic Quality & Teaching

_QS: Faculty/Student Ratio 20% | THE: Teaching 30% (staff-to-student, doctorate ratio)_

| KPI ID   | Name                                   | Formula / Source                                                        | Ranking Signal                | Frequency |
| -------- | -------------------------------------- | ----------------------------------------------------------------------- | ----------------------------- | --------- |
| `ACA-01` | Student-Faculty Ratio                  | Total enrolled students ÷ FTE academic staff                            | **QS 20% · THE 4.5%**         | Semester  |
| `ACA-02` | Success Rate                           | Students who passed all modules ÷ total enrolled (per cohort)           | Internal · THE Teaching proxy | Semester  |
| `ACA-03` | Dropout Rate                           | Students who withdrew without graduating ÷ cohort size                  | Internal governance           | Semester  |
| `ACA-04` | Repetition Rate                        | Students repeating a year ÷ total enrolled                              | Internal governance           | Semester  |
| `ACA-05` | Curriculum Coverage Rate               | Actual delivered hours ÷ minimum required hours per module (%)          | ISO 21001 · Internal          | Semester  |
| `ACA-06` | Faculty with PhDs (%)                  | Faculty holding doctoral degree ÷ total faculty                         | THE Teaching · QS regional    | Annual    |
| `ACA-07` | Double Degree Programs                 | Count of active double-degree agreements with foreign institutions      | Internationalization proxy    | Annual    |
| `ACA-08` | Professional Certifications (students) | Students holding industry certifications ÷ enrolled                     | Employability proxy           | Annual    |
| `ACA-09` | Accredited Programs                    | Programs holding external accreditation ÷ total programs                | Internal quality              | Annual    |
| `ACA-10` | Average Grade Performance Index        | Mean GPA / weighted exam score across institution                       | Internal governance           | Semester  |
| `ACA-11` | Absenteeism Rate (students)            | Unexcused absences ÷ total class hours                                  | Internal governance           | Monthly   |
| `ACA-12` | Weak Student Remediation Rate          | At-risk students receiving formal support ÷ identified at-risk students | ISO 21001                     | Semester  |

---

##### DOMAIN C — Employability & Industry Relations

_QS: Employer Reputation 10% + Employment Outcomes 5% | THE: Industry Income 2.5%_

| KPI ID   | Name                                   | Formula / Source                                                            | Ranking Signal            | Frequency |
| -------- | -------------------------------------- | --------------------------------------------------------------------------- | ------------------------- | --------- |
| `EMP-01` | Graduate Employment Rate               | Graduates employed within 12 months ÷ graduates surveyed                    | **QS 10%+5%**             | Annual    |
| `EMP-02` | Employer Reputation Score              | Weighted score from employer survey responses (structured survey)           | **QS 10%**                | Annual    |
| `EMP-03` | Time to First Employment               | Median months from graduation to first job (survey)                         | QS Employment Outcomes    | Annual    |
| `EMP-04` | Industry Partnership Count             | Active formal agreements with private sector entities                       | THE Industry Income proxy | Annual    |
| `EMP-05` | Internship Placement Rate              | Students completing required internships ÷ enrolled final-year students     | Internal · QS EO proxy    | Semester  |
| `EMP-06` | PFE (Final Year Project) Industry Rate | PFE projects hosted by industry ÷ total PFE                                 | Internal governance       | Annual    |
| `EMP-07` | Alumni Engagement Rate                 | Alumni responding to survey or participating in events ÷ total alumni (5yr) | QS EO proxy               | Annual    |
| `EMP-08` | Career Services Utilization            | Students using career center services ÷ enrolled                            | Internal governance       | Semester  |

---

##### DOMAIN D — Internationalization

_QS: International Faculty Ratio 5% + International Student Ratio 5% + International Research Network 5%_

| KPI ID   | Name                                 | Formula / Source                                                   | Ranking Signal       | Frequency |
| -------- | ------------------------------------ | ------------------------------------------------------------------ | -------------------- | --------- |
| `INT-01` | International Faculty Ratio          | Faculty with foreign nationality or foreign degree ÷ total faculty | **QS 5%**            | Annual    |
| `INT-02` | International Student Ratio          | Students with foreign nationality ÷ total enrolled                 | **QS 5%**            | Semester  |
| `INT-03` | Outgoing Student Mobility            | Students participating in exchange/Erasmus ÷ enrolled              | Internationalization | Annual    |
| `INT-04` | Incoming Student Mobility            | Foreign students on exchange at institution ÷ enrolled             | Internationalization | Annual    |
| `INT-05` | International Partnership Agreements | Active MOU/convention with foreign universities                    | QS IRN proxy         | Annual    |
| `INT-06` | Foreign Language Program Rate        | Programs taught fully or partially in a foreign language ÷ total   | Internationalization | Annual    |

---

##### DOMAIN E — Finance & Resources

_THE: Industry Income 2.5% · Institutional Income 2.25% | Internal governance_

| KPI ID   | Name                          | Formula / Source                                            | Ranking Signal            | Frequency |
| -------- | ----------------------------- | ----------------------------------------------------------- | ------------------------- | --------- |
| `FIN-01` | Budget Execution Rate         | Actual expenditure ÷ allocated budget (%)                   | Internal governance       | Monthly   |
| `FIN-02` | Cost per Student              | Total operating expenditure ÷ enrolled students             | Internal governance       | Annual    |
| `FIN-03` | Research Funding Ratio        | External research funding ÷ total budget                    | THE Research Income proxy | Annual    |
| `FIN-04` | Revenue Diversification Index | Non-public-funding revenue ÷ total revenue                  | Internal governance       | Annual    |
| `FIN-05` | Inventory Utilization Rate    | Assets in active use ÷ total registered assets              | Internal operations       | Semester  |
| `FIN-06` | Project Budget Compliance     | Projects delivered within budget ÷ total completed projects | Internal governance       | Annual    |
| `FIN-07` | Payroll Accuracy Rate         | Payslips issued without correction ÷ total payslips         | Internal HR               | Monthly   |

---

##### DOMAIN F — Human Resources

_THE: Teaching (staff-to-student) · QS: Faculty/Student Ratio | Internal governance_

| KPI ID  | Name                                   | Formula / Source                                                    | Ranking Signal      | Frequency |
| ------- | -------------------------------------- | ------------------------------------------------------------------- | ------------------- | --------- |
| `HR-01` | Professor Workload Compliance Rate     | Faculty within ±20% of contracted hours ÷ total faculty             | Internal governance | Monthly   |
| `HR-02` | Teaching Load Balance Index            | Std. deviation of hours across faculty (lower = better)             | Internal governance | Semester  |
| `HR-03` | Professor-per-Student Ratio            | FTE faculty ÷ enrolled students (inverted of ACA-01)                | **QS 20%**          | Semester  |
| `HR-04` | Administrative Staff per Student       | Admin FTE ÷ enrolled students                                       | Internal governance | Annual    |
| `HR-05` | Faculty Training Fulfillment Rate      | Training hours completed ÷ training hours required                  | ISO 21001           | Annual    |
| `HR-06` | Absenteeism Rate (staff)               | Unexcused absences ÷ scheduled days                                 | Internal governance | Monthly   |
| `HR-07` | Vacancy Fill Time                      | Days from position open to contract signed                          | Internal HR         | Per-event |
| `HR-08` | Permanent-to-Contractual Faculty Ratio | Permanent faculty ÷ total faculty                                   | Internal governance | Annual    |
| `HR-09` | Faculty Expertise Match Rate           | Faculty whose specialization matches their assigned courses ÷ total | Internal quality    | Semester  |

---

##### DOMAIN G — Sustainability & ESG

_QS: Sustainability 5% | THE: Sustainability 7.5%_

| KPI ID   | Name                           | Formula / Source                                            | Ranking Signal                 | Frequency |
| -------- | ------------------------------ | ----------------------------------------------------------- | ------------------------------ | --------- |
| `ESG-01` | Energy Consumption per Student | kWh consumed ÷ enrolled students                            | **QS/THE Sustainability**      | Monthly   |
| `ESG-02` | Carbon Footprint per Student   | CO2e kg ÷ enrolled students                                 | **QS/THE Sustainability**      | Annual    |
| `ESG-03` | Renewable Energy Rate          | Renewable energy consumed ÷ total energy consumed           | QS/THE Sustainability          | Annual    |
| `ESG-04` | Recycling Rate                 | Waste recycled ÷ total waste generated                      | QS/THE Sustainability          | Annual    |
| `ESG-05` | Green Transportation Rate      | Students/staff using sustainable transport ÷ total (survey) | QS/THE Sustainability          | Annual    |
| `ESG-06` | Campus Accessibility Score     | Accessibility-compliant facilities ÷ total facilities       | QS/THE Sustainability (Social) | Annual    |
| `ESG-07` | Gender Diversity Index         | Female faculty ÷ total faculty                              | QS/THE Sustainability (Social) | Annual    |
| `ESG-08` | SDG-Aligned Research Rate      | Publications linked to UN SDGs ÷ total publications         | THE Sustainability             | Annual    |

---

##### DOMAIN H — Governance & Compliance (Internal only)

_ISO 21001:2018 alignment — no direct ranking contribution but required for accreditation_

| KPI ID   | Name                                  | Formula / Source                                                      | Frequency |
| -------- | ------------------------------------- | --------------------------------------------------------------------- | --------- |
| `GOV-01` | ISO 21001 Document Control Compliance | Controlled documents current ÷ total controlled documents             | Monthly   |
| `GOV-02` | Internal Audit NCR Closure Rate       | Closed non-conformances ÷ total NCRs raised (90-day window)           | Quarterly |
| `GOV-03` | Governance Meeting Frequency          | Actual BOS/DAB/PAC meetings ÷ required meetings (per charter)         | Semester  |
| `GOV-04` | Risk Register Currency                | Days since last risk register update (target: ≤ 30 days)              | Monthly   |
| `GOV-05` | Stakeholder Feedback Action Rate      | Feedback items with closed action ÷ total feedback received           | Semester  |
| `GOV-06` | Document Completeness Index           | Required institutional documents present and current ÷ total required | Monthly   |

---

### 4.3 Ranking Score Computation

#### Composite Score Formula

Each institution receives a **UCAR Score** (0–100) computed as a weighted composite. The weights below are derived from QS methodology with pragmatic adjustment for measurability at UCAR's current data maturity.

```
UCAR_Score = Σ (normalized_kpi_score_i × weight_i)
```

Where each KPI is normalized to [0, 100] relative to the best-performing UCAR institution (percentile normalization within the network):

```
normalized_score_i = (institution_value_i - min_network_i) / (max_network_i - min_network_i) × 100
```

**Weight table (sum = 100)**

| Domain                      | UCAR Weight | Primary Ranking Proxy        |
| --------------------------- | ----------- | ---------------------------- |
| Research & Citations        | 25%         | QS CPF 20% + IRN 5%          |
| Academic Quality & Teaching | 20%         | QS FSR 20% · THE Teaching    |
| Employability & Industry    | 18%         | QS ER 10% + EO 5% + Industry |
| Internationalization        | 12%         | QS IFR 5% + ISR 5% + IRN     |
| Finance & Resources         | 10%         | THE Income indicators        |
| Human Resources             | 8%          | QS/THE Staff ratios          |
| Sustainability & ESG        | 5%          | QS/THE Sustainability        |
| Governance & Compliance     | 2%          | ISO 21001 (internal only)    |

> **Implementation note**: Weights are stored in the database table `ucar_global.kpi_weights` and can be adjusted by an authorized administrator without a code deployment. Each weight change is version-controlled with an effective date.

#### UCAR Network Ranking

Institutions are ranked 1–35 by their UCAR Score. The ranking is recomputed on each full KPI batch completion (typically weekly). Rank delta vs. previous period is displayed prominently.

#### International Ranking Predictor

A secondary computed score maps UCAR KPIs to the exact QS indicator definitions and outputs a **predicted QS band** (e.g., "501–600") using a regression model trained on historical QS data for comparable institutions. This is a **prediction, not a guarantee** and is labeled accordingly.

```
predicted_qs_score = f(RES-01, ACA-01, EMP-01, EMP-02, INT-01, INT-02, INT-04, ESG-*)
```

Model: Ridge regression with SHAP explainability. Retrained annually when new QS data is published.

---

### 4.4 Dashboard Specification

#### Views

**1. University President View** (cross-institution)

- Ranked leaderboard of all 35 institutions by UCAR Score
- Domain radar charts: each institution's 8-domain profile
- UCAR network aggregate score vs. last period
- Predicted QS band for UCAR as a network
- Top 5 anomalies (institutions with largest negative KPI deltas)
- Drill-down: click any institution → Dean View

**2. Dean View** (single institution)

- Institution UCAR Score + rank (#N of 35) + delta
- KPI cards for each domain with traffic-light status (green/amber/red)
- Time-series chart per KPI (configurable period)
- Comparison panel: institution vs. UCAR median vs. UCAR best
- Alert feed (institution-specific)
- Missing document warnings (feeds from doc-service)

**3. KPI Detail View**

- Full time-series for one KPI
- Data lineage: which documents contributed to this value
- Last computation timestamp + source institution data
- SHAP contribution breakdown (for AI-derived metrics)

**4. Ranking Simulation View** (President only)

- Adjust hypothetical KPI values → see predicted UCAR Score impact
- "What-if" slider for each domain weight

#### Technical requirements

- All charts use Recharts with server-side aggregated data (no raw data to client)
- KPI cards refresh every 5 minutes via WebSocket subscription
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

#### Stage 5: Storage

```
Each extracted record stored as:
  - Raw file → MinIO bucket (immutable, versioned)
  - Extracted JSON → PostgreSQL table `documents.extracted_records`
  - Full text → Elasticsearch index `docs-{tenant}`
  - Extraction metadata → `documents.ingestion_log` (confidence, strategy, reviewer)
```

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
│   ├── minio_client.py     # Raw file storage
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
  contract_type   VARCHAR(20) NOT NULL CHECK (contract_type IN ('permanent', 'contractual')),
  rank            VARCHAR(50),       -- Maître assistant A/B, Maître de conférences, Professeur
  position_status VARCHAR(20),       -- active, on_leave, suspended, retired
  hire_date       DATE,
  min_hours       INTEGER,           -- contractual minimum teaching hours/semester
  max_hours       INTEGER,           -- overwork threshold
  base_salary     NUMERIC(12,3),
  photo_url       TEXT,
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
  document_url    TEXT               -- link to uploaded diploma in MinIO
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
  h_index_contrib BOOLEAN DEFAULT false,
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

#### Use case 2: Ambassador Program matching

Identify professors best suited to represent UCAR in external academic networks:

```
Criteria:
  - International publications (RES-04 contributor)
  - Foreign language proficiency (from profile)
  - Active international collaborations
  - H-index above institution median
  - No disciplinary flags

Output: ranked list of "Ambassador Eligible" faculty per domain
```

#### Use case 3: Promotion eligibility

```
Permanent professor promotion criteria (per Tunisian statute):
  - Years in current rank ≥ minimum tenure
  - Hours delivered ≥ required (no deficit)
  - Publications meeting threshold for target rank
  - No pending disciplinary action

System outputs: "Eligible for promotion" / "Eligible in N months" / "Not eligible: [reasons]"
```

### 6.4 Hiring Workflows

#### Permanent Professor Hiring (UCAR/Ministry Concours)

Current process: manual, opaque, error-prone. Digitalized flow:

```
Phase 1: Position Opening
  - UCAR HR posts vacancy (institution, rank, specialization, N seats)
  - System publishes to ministry platform (API integration)
  - Deadline and test date configured

Phase 2: Candidate Application
  - Candidates upload dossier via public portal (no auth required)
  - Dossier: CV, diplomas, publications list, identity document
  - Auto-validation: required documents present? → flagged if not
  - Dossier classified and stored in doc-service

Phase 3: Eligibility Screening
  - System auto-checks: degree level, years of experience (from CV NLP extraction)
  - Ineligible candidates flagged with reason
  - Eligible candidates admitted to written test phase

Phase 4: Written Test & Results
  - Test administered externally (paper or online)
  - Results uploaded as document → doc-service extracts scores
  - Candidates ranked by test score

Phase 5: Institution Preference & Assignment
  [This is the key automation target]

  Current: manual negotiation after results

  Automated:
  - Passing candidates rank their preferred institutions (up to 4 choices)
  - System runs stable matching algorithm (Gale-Shapley variant):
    - Candidate preference list: their 4 choices in order
    - Institution preference: ranked by test score + specialization match score
  - Assignment output: each candidate matched to one institution or unmatched
  - Human override possible: Dean can swap two matched candidates with audit log
  - Assignments published and candidates notified automatically

Phase 6: Contract Issuance
  - HR uploads contract template → auto-filled with candidate and position data
  - Contract sent for e-signature (DocuSign API or equivalent)
  - Signed contract stored in doc-service, professor record created
```

#### Contractual Professor Hiring (Institution-managed)

```
Phase 1: Position Opening
  - Institution HR posts vacancy in platform
  - Publicly visible: title, required hours, specialization, compensation band

Phase 2: Dossier Upload
  - Candidates register and upload dossier
  - Fields: CV, degrees, publications, reference letters, cover letter
  - System auto-scores dossier: matching-score against position requirements
  - HR sees ranked candidate list before interviews

Phase 3: Interview Scheduling
  - HR selects candidates for interview from ranked list
  - Calendar integration: interview slots proposed, candidate confirms
  - Interview outcomes recorded (pass/fail + notes)

Phase 4: Selection & Offer
  - HR selects candidate from interviewed pool (override of AI ranking possible)
  - Offer letter auto-generated from template
  - E-signature workflow

Phase 5: Onboarding
  - Professor record created automatically
  - Required documents checklist sent to professor
  - First-semester course assignments suggested by matching engine
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

## 9. Module 6 — Nice-to-Have Features

These features are explicitly lower priority but architecturally compatible with the core platform. They share the same data layer and services.

### 9.1 Automated Reports & Email Digests

- **Weekly digest**: Every Monday 08:00 — KPI summary, top 3 alerts, rank delta. Sent to Dean (institution) and President (network).
- **Monthly synthesis**: Full KPI report for each institution. PDF export. MESRS-compatible format.
- **Annual ranking report**: Full UCAR network analysis. Predicted QS/THE bands. Trend analysis. Board-ready format.
- **On-demand**: Any dashboard view exportable to PDF in one click (server-side rendering via Puppeteer/WeasyPrint).

Implementation: Celery beat scheduler → `report-service` → MinIO storage → email dispatch.

### 9.2 Predicted International Ranking

- **Model**: Ridge regression trained on historical QS data for comparable MENA institutions
- **Inputs**: QS-mappable KPIs from the catalog (RES-01, ACA-01, EMP-01, EMP-02, INT-01, INT-02, RES-04, ESG composite)
- **Outputs**: Predicted QS band (e.g., "801-1000"), THE band, confidence interval
- **Display**: Separate "Ranking Intelligence" panel on President dashboard
- **Explainability**: "To move from 801-1000 to 701-800, focus on: Citations per Faculty (+35%), International Faculty Ratio (+8%)"
- **Update frequency**: On new QS data publication (annual); UCAR KPI inputs refresh weekly

### 9.3 Document Anomaly Detection

(Architecturally part of doc-service — surfaced in Alerts)

- **OCR failure detection**: Character confidence < threshold; layout recognition failure
- **Human entry errors**: Values outside statistical range for document class
- **Duplicate detection**: Near-identical documents submitted for different periods
- **Tampering signals**: Metadata inconsistency (PDF creation date vs. claimed report date)
- **Language inconsistency**: French document with embedded Arabic field values incorrectly OCR'd

All anomalies surfaced in Alert module at WARNING level with document link and field annotation.

### 9.4 Natural Language Queries

Powered by `nlp-service` using RAG (Retrieval-Augmented Generation) over the Elasticsearch document index:

**Example queries:**

- "Quels sont les taux d'abandon par institution ce semestre ?"
- "Compare le budget d'INSAT et d'IHEC sur les 3 dernières années."
- "Montre-moi tous les PV de réunion du conseil scientifique de FSB depuis 2023."
- "Which professors at ENICarthage are eligible for promotion this year?"
- "What is the h-index distribution across UCAR research labs?"

**Architecture:**

```
User query
    │
    ▼
Query classifier → intent: [kpi_query | document_search | comparison | narrative]
    │
    ├── kpi_query → SQL generation → PostgreSQL → response
    ├── document_search → Elasticsearch search → top-k docs → LLM synthesis
    ├── comparison → multi-institution KPI pull → LLM narrative
    └── narrative → structured report generation
    │
    ▼
Response generator (Claude API)
  - Bilingual (fr/ar) response
  - Cited sources: document IDs / KPI computation timestamps
  - Suggested follow-up questions
```

---

## 10. Data Models

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
CREATE TABLE kpi_records (
  id              UUID PRIMARY KEY,
  tenant_id       UUID REFERENCES tenants(id),
  kpi_id          VARCHAR(10) REFERENCES kpi_definitions(kpi_id),
  value           NUMERIC(15,4),
  normalized_score NUMERIC(5,2),   -- 0-100
  period_start    DATE,
  period_end      DATE,
  computed_at     TIMESTAMPTZ,
  source_doc_ids  UUID[],          -- traceability
  computation_log JSONB,           -- intermediate values for audit
  is_estimated    BOOLEAN DEFAULT false  -- true if imputed from incomplete data
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
  predicted_qs_band VARCHAR(30),
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
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 10.2 Document Tables (`documents` schema)

```sql
CREATE TABLE documents.files (
  id              UUID PRIMARY KEY,
  tenant_id       UUID REFERENCES ucar_global.tenants(id),
  original_name   TEXT NOT NULL,
  storage_path    TEXT NOT NULL,   -- MinIO path
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

## 11. API Contract Reference

All APIs follow REST conventions. Base URL: `https://api.ucar-erp.tn/v1/`

Authentication: `Authorization: Bearer {jwt_token}` on all requests.

Tenant scoping: Injected from JWT claims. Cross-tenant requests require `X-Global-Scope: true` header and `GLOBAL_READ` permission.

### Key Endpoint Groups

```
/auth/
  POST /auth/login                    → JWT token
  POST /auth/refresh                  → New JWT token
  GET  /auth/me                       → Current user profile + permissions

/kpi/
  GET  /kpi/definitions               → Full KPI catalog
  GET  /kpi/records?period=&domain=   → KPI values for current tenant
  GET  /kpi/records/{kpi_id}/trend    → Time-series for one KPI
  GET  /kpi/scores/institution        → UCAR Score for current tenant
  GET  /kpi/scores/network            → All institution scores (GLOBAL_READ)
  GET  /kpi/simulate                  → Ranking simulation (what-if)
  POST /kpi/recompute                 → Trigger manual KPI recomputation (admin)

/documents/
  POST /documents/upload              → Upload file (multipart)
  GET  /documents/                    → List documents for tenant
  GET  /documents/{id}                → Document metadata
  GET  /documents/{id}/download       → Pre-signed MinIO URL
  GET  /documents/review/queue        → Pending human review items
  POST /documents/review/{id}/approve → Approve extraction result
  POST /documents/review/{id}/reject  → Reject + annotate
  GET  /documents/templates/          → List templates
  POST /documents/templates/          → Create template
  POST /documents/migrate/batch       → Start batch migration job

/hr/
  GET  /hr/professors/                → List professors (tenant-scoped)
  POST /hr/professors/                → Create professor record
  GET  /hr/professors/{id}            → Professor profile
  PUT  /hr/professors/{id}            → Update professor record
  GET  /hr/professors/{id}/hours      → Workload data
  GET  /hr/professors/match           → Matching suggestions for a course
  GET  /hr/professors/eligible-promotions → Promotion eligibility list

/hiring/
  GET  /hiring/positions/             → Open positions
  POST /hiring/positions/             → Create position (HR Manager)
  POST /hiring/applications/          → Submit application (public, no auth)
  GET  /hiring/applications/          → List applications (HR Manager)
  POST /hiring/applications/{id}/advance → Move to next phase
  POST /hiring/permanent/match        → Run Gale-Shapley assignment

/projects/
  GET  /projects/                     → Project board
  POST /projects/                     → Post new project
  GET  /projects/{id}/matches         → Institution match results
  POST /projects/{id}/assign          → Assign project to institution

/alerts/
  GET  /alerts/                       → Alert feed (tenant-scoped or global)
  GET  /alerts/{id}                   → Alert detail
  POST /alerts/{id}/resolve           → Mark resolved
  GET  /alerts/thresholds/            → Current threshold config
  PUT  /alerts/thresholds/{kpi_id}    → Update threshold

/reports/
  POST /reports/generate              → On-demand report generation
  GET  /reports/                      → Report history
  GET  /reports/{id}/download         → Pre-signed URL for PDF/Excel

/nlp/
  POST /nlp/query                     → Natural language query
  POST /nlp/query/document            → Query over a specific document
```

### Standard Error Format

```json
{
  "error": {
    "code": "KPI_INSUFFICIENT_DATA",
    "message_fr": "Données insuffisantes pour calculer ce KPI.",
    "message_ar": "بيانات غير كافية لحساب مؤشر الأداء هذا.",
    "detail": "RES-01 requires at least 1 approved publication_list document for period 2025-S1",
    "tenant_id": "uuid",
    "kpi_id": "RES-01"
  }
}
```

---

## 12. Multi-Tenancy & Security

### 12.1 Permission Matrix

| Permission            | Student | Faculty | Admin Staff | Dean | President | IT Admin | MESRS Auditor |
| --------------------- | ------- | ------- | ----------- | ---- | --------- | -------- | ------------- |
| View own KPIs         | ✓       | ✓       | ✓           | ✓    | ✓         | ✓        | —             |
| View institution KPIs | —       | limited | ✓           | ✓    | ✓         | ✓        | read-only     |
| View all institutions | —       | —       | —           | —    | ✓         | ✓        | aggregated    |
| Upload documents      | —       | ✓       | ✓           | ✓    | —         | ✓        | —             |
| Approve extractions   | —       | —       | ✓           | ✓    | —         | ✓        | —             |
| Configure thresholds  | —       | —       | —           | ✓    | ✓         | ✓        | —             |
| Manage users          | —       | —       | —           | —    | —         | ✓        | —             |
| Trigger KPI recompute | —       | —       | —           | —    | —         | ✓        | —             |
| Export MESRS report   | —       | —       | —           | ✓    | ✓         | ✓        | ✓             |
| Post projects         | —       | —       | —           | ✓    | ✓         | ✓        | —             |
| Manage hiring         | —       | —       | HR Mgr      | ✓    | ✓         | ✓        | —             |

### 12.2 Row-Level Security

PostgreSQL RLS policies enforce tenant isolation at the database level. Even if application code is compromised, a query from tenant A cannot return tenant B's rows:

```sql
ALTER TABLE kpi_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON kpi_records
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

The application layer sets `app.current_tenant` from the JWT claims at the start of every database session.

### 12.3 Audit Log

Every write operation is logged to an immutable audit table:

```sql
CREATE TABLE ucar_global.audit_log (
  id          UUID PRIMARY KEY,
  user_id     UUID,
  tenant_id   UUID,
  action      VARCHAR(50),   -- CREATE, UPDATE, DELETE, EXPORT, LOGIN
  entity_type VARCHAR(50),
  entity_id   UUID,
  old_value   JSONB,
  new_value   JSONB,
  ip_address  INET,
  user_agent  TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);
```

Retention: 5 years (partitioned monthly, archived to cold storage after 1 year).

---

## 13. Deployment Topology

### 13.1 Environments

| Environment  | Purpose                            | Scale                          |
| ------------ | ---------------------------------- | ------------------------------ |
| `local`      | Developer machine (Docker Compose) | Single node, mocked ML models  |
| `staging`    | Pre-production testing (K8s)       | 3-node cluster, 2 mock tenants |
| `production` | Live system                        | Auto-scaling, 35+ tenants      |

### 13.2 Docker Compose (Local Development)

```yaml
# docker-compose.yml (abbreviated)
services:
  api-gateway: # nginx reverse proxy
  kpi-service: # FastAPI
  doc-service: # FastAPI
  hr-service: # FastAPI
  alert-service: # FastAPI
  nlp-service: # FastAPI
  report-service: # FastAPI
  auth-service: # Keycloak
  worker: # Celery worker
  beat: # Celery beat scheduler
  postgres: # PostgreSQL + TimescaleDB
  redis: # Redis
  minio: # MinIO object store
  elasticsearch: # Elasticsearch
  frontend: # React dev server
  grafana: # Observability
  prometheus: # Metrics
```

### 13.3 Kubernetes Production (Abbreviated)

- Each service: Deployment + HorizontalPodAutoscaler (min 2, max 10 replicas)
- PostgreSQL: Managed instance (e.g., AWS RDS / Azure Database) or Crunchy Data PGO on K8s
- MinIO: StatefulSet or managed object storage
- Elasticsearch: ECK operator
- Secrets: Kubernetes Secrets + external secrets manager (Vault or AWS Secrets Manager)
- Ingress: nginx ingress controller with TLS termination
- Networking: NetworkPolicy enforcing service-to-service isolation

---

## 14. Implementation Roadmap

### Phase 1 — Foundation (Weeks 1–4)

_Goal: auth, tenant management, first KPI ingestion, document upload_

- [ ] Auth service: JWT, RBAC, Keycloak integration
- [ ] Tenant provisioning: admin UI to create institutions
- [ ] Document upload: MinIO integration, format normalizer, basic classifier
- [ ] KPI definitions loaded: all KPI catalog entries seeded
- [ ] Manual KPI entry: admin can input KPI values directly (bootstrap before full pipeline)
- [ ] Basic dashboard: KPI cards, no time-series yet
- [ ] PostgreSQL multi-schema setup with RLS

### Phase 2 — Document Intelligence (Weeks 5–8)

_Goal: working extraction pipeline for 5 core document classes_

- [ ] OCR pipeline: Tesseract + LLM post-correction
- [ ] Extractors for: grade_sheet, budget_report, faculty_record, syllabus, publication_list
- [ ] Human review queue UI
- [ ] Template engine + batch migration CLI
- [ ] Extraction results → KPI auto-computation for covered KPIs
- [ ] Document anomaly detection (basic)
- [ ] Elasticsearch full-text index of extracted documents

### Phase 3 — KPI Engine & Dashboard (Weeks 9–12)

_Goal: full KPI computation, ranking, dashboard complete_

- [ ] Full KPI computation engine (all 8 domains)
- [ ] TimescaleDB integration for time-series
- [ ] Institution ranking + composite score
- [ ] Comparative views (institution vs. network)
- [ ] International ranking predictor (regression model)
- [ ] President + Dean + KPI detail views complete
- [ ] PDF/Excel export for all views

### Phase 4 — HR & Alerts (Weeks 13–16)

_Goal: professor management and alert system live_

- [ ] Professor profile CRUD + bulk import
- [ ] Workload tracking + gauge dashboards
- [ ] Matching engine (module-to-professor)
- [ ] Alert engine: threshold monitoring + notification dispatch
- [ ] Mini audit report generation
- [ ] Predictive alerts (ML models: dropout, budget overrun)

### Phase 5 — Hiring, Projects & NLP (Weeks 17–20)

_Goal: hiring workflows, project matching, natural language queries_

- [ ] Permanent hiring workflow (Gale-Shapley matching)
- [ ] Contractual hiring workflow
- [ ] Project posting + KPI-based matching
- [ ] NLP query interface (RAG over document index)
- [ ] Automated scheduled reports
- [ ] Mobile app (React Native) — MVP scope

### Phase 6 — Hardening & Go-Live (Weeks 21–24)

_Goal: production-ready at scale_

- [ ] Load testing (35 tenants, 5 years of historical data)
- [ ] Security audit + penetration testing
- [ ] Arabic RTL QA across all views
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Staff training materials + video tutorials
- [ ] Runbook documentation
- [ ] MESRS integration API (report export)
- [ ] Production deployment

---

## 15. Open Questions & Constraints

### Unresolved Technical Questions

| #   | Question                                                                          | Impact                             | Owner                |
| --- | --------------------------------------------------------------------------------- | ---------------------------------- | -------------------- |
| Q1  | Will UCAR provide API access to the national inscription portal (inscription.tn)? | ACA-02, ACA-03, INT-02 data source | UCAR IT              |
| Q2  | Scopus / Web of Science API access — institutional subscription?                  | RES-01, RES-02, RES-09             | UCAR Research Office |
| Q3  | Does Keycloak need to federate with Ministry LDAP/Active Directory?               | SSO for permanent staff            | Ministry IT          |
| Q4  | Is IoT sensor infrastructure available on any UCAR campus?                        | ESG-01, ESG-02, ESG-03             | Facilities           |
| Q5  | Budget for cloud infrastructure vs. on-premise?                                   | Deployment topology                | UCAR Admin           |
| Q6  | Are employer surveys to be conducted by UCAR or sourced from QS directly?         | EMP-01, EMP-02                     | External Relations   |
| Q7  | Legal basis for storing professor personal data (Tunisian Law 63-2004)?           | HR module compliance               | Legal counsel        |

### Known Constraints

- **Network reliability**: Some UCAR campuses (Bizerte, Nabeul) have inconsistent connectivity. Read-only offline mode with 24h KPI cache is mandatory.
- **Arabic OCR quality**: Tesseract Arabic accuracy degrades on handwritten text. GPT-4o vision fallback adds latency and cost. Budget allocation needed.
- **QS Academic Reputation (40% weight)**: Cannot be computed internally — requires global academic survey. The platform tracks the _other_ 60% of QS indicators and flags reputation as "survey-based, tracked externally."
- **Data maturity lag**: Year 1 KPIs will be partially computed (missing data from non-digitalized documents). System must handle partial computation gracefully with confidence intervals, not zero values.
- **Gale-Shapley output is advisory**: Ministry retains final authority on permanent professor assignments. Platform generates recommendation; human override with mandatory audit log.

### Spec Documents To Be Written

Each of the following will be a separate `specs/{service}.md` file with: data model detail, endpoint specs, LLM prompt templates, test cases, and edge case handling:

- [ ] `specs/kpi-service.md`
- [ ] `specs/doc-service.md`
- [ ] `specs/hr-service.md`
- [ ] `specs/project-service.md`
- [ ] `specs/alert-service.md`
- [ ] `specs/nlp-service.md`
- [ ] `specs/report-service.md`
- [ ] `specs/auth-service.md`
- [ ] `specs/admin-service.md`
- [ ] `specs/frontend.md`
- [ ] `specs/ml-models.md`
- [ ] `specs/migration-playbook.md`

---

_End of UCAR ERP Master Document v1.0_  
_Next: `specs/kpi-service.md` — detailed KPI computation engine specification_
