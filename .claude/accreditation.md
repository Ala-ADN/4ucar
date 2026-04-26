# Accreditation Compliance Engine — Implementation Specification

> **Status:** v1.0 · April 2026  
> **Service:** `accreditation-service`  
> **Analogues:** Vanta (SOC 2 / ISO 27001), Drata, Sprinto — adapted for university accreditation and ranking frameworks

---

## 1. Mental Model

The accreditation engine maps UCAR's operational reality onto the requirements of external frameworks the university aspires to satisfy — exactly as enterprise compliance tools map an organization's controls and policies onto SOC 2 or ISO 27001. The core loop is:

```
Framework defines Controls
  → Each Control has one or more Tests
      → Tests are satisfied by Evidence
          → Evidence comes from ingested Documents (via Templates) and computed KPIs
              → Document approval triggers automatic test re-evaluation
                  → Control status updates in real time
```

The platform never predicts a score. It answers one question per control: **"Do we have sufficient, approved evidence that this requirement is currently met — and if not, exactly what is missing?"**

---

## 2. Core Entities

### 2.1 Framework

An external accreditation body or ranking methodology that defines requirements UCAR wants to satisfy.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `code` | VARCHAR(20) | `ISO9001`, `ISO21001`, `GREENMETRIC` |
| `name_fr` / `name_ar` | TEXT | Bilingual display name |
| `version` | VARCHAR(20) | e.g. `2025` — frameworks update annually |
| `description` | TEXT | What this framework measures and who uses it |
| `scope` | VARCHAR(20) | `INSTITUTION`: control evaluated independently per institution. `NETWORK`: control evaluated at UCAR network level — the aggregate across all institutions is what satisfies the control (e.g. QS-CPF is the network-wide citations/faculty ratio, not per-institution). `control_status` records for NETWORK-scoped controls use `tenant_id = NULL` for the aggregate status, plus one row per institution showing that institution's evidence contribution. |
| `is_active` | BOOLEAN | Inactive frameworks are archived, not deleted |

**Frameworks in scope (demo):**

| Code | Name | Scope | Controls | Notes |
|---|---|---|---|---|
| `ISO9001` | ISO 9001:2015 Quality Management System | INSTITUTION | 10 clauses | Generic QMS — document control, risk management, internal audit, nonconformity. Foundational layer that ISO 21001 extends. |
| `ISO21001` | ISO 21001:2018 Educational Organization Management System | INSTITUTION | 12 key clauses | EOMS — extends ISO 9001 for educational orgs: learner-focused requirements, curriculum design, competence management, student performance monitoring. |
| `GREENMETRIC` | UI GreenMetric World University Rankings | NETWORK | 6 categories | Setting & Infrastructure, Energy & Climate Change, Waste, Water, Transport, Education & Research. Evidence: energy reports, sustainability surveys, transport surveys. |

---

### 2.2 Control

The atomic requirement within a framework — equivalent to a "control" in Vanta or a "criterion" in accreditation audit language.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `framework_id` | UUID | |
| `code` | VARCHAR(30) | e.g. `ISO9001-7.5`, `ISO21001-8.2`, `GM-ENERGY` |
| `name_fr` / `name_ar` | TEXT | |
| `description` | TEXT | What the framework body officially requires |
| `category` | VARCHAR(100) | Grouping within the framework (e.g. "Research", "Teaching", "Governance") |
| `weight` | NUMERIC(5,4) | This control's weight in the framework's composite score (0.0–1.0, sum = 1.0) |
| `passing_threshold` | NUMERIC | Value at or above which the control is PASSING (for quantitative controls) |
| `warning_threshold` | NUMERIC | Value below passing but above failing — control is NEEDS_EVIDENCE or FAILING |
| `unit` | VARCHAR(50) | `ratio`, `percent`, `count`, `binary`, `score` |
| `official_methodology` | TEXT | How the framework body officially computes or evaluates this control |
| `requires_external_survey` | BOOLEAN | True for controls whose primary evidence is an externally-conducted survey result (QS Academic/Employer Reputation). These use a DOCUMENT_UPLOAD test — the institution uploads the received survey result document. NOT_APPLICABLE is only set if the institution explicitly marks it so (e.g. they did not participate). |
| `owner_role` | VARCHAR(50) | Role responsible for ensuring this control is satisfied (`DEAN`, `HR_MANAGER`, `RESEARCH_OFFICE`, etc.) |

---

### 2.3 Test

Each control has one or more tests. A control is PASSING when **all required tests** pass (or all non-waived tests pass). Tests are the atomic verification units — equivalent to Vanta's automated and manual tests.

**Test types:**

| Type | How it passes | Example |
|---|---|---|
| `AUTOMATED_KPI` | KPI computed value meets threshold | Citations/Faculty ≥ 5.0 (RES-01) |
| `DOCUMENT_UPLOAD` | At least N approved documents of a required template type are on file for the relevant period | At least 1 approved `publication_list` document for current academic year |
| `ATTESTATION` | Authorized staff has submitted a signed attestation for the current period | Dean attests that governance meetings occurred as scheduled |

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `control_id` | UUID | |
| `name` | TEXT | Human-readable test description |
| `test_type` | VARCHAR(20) | `AUTOMATED_KPI`, `DOCUMENT_UPLOAD`, `ATTESTATION` |
| `kpi_id` | VARCHAR(10) | For AUTOMATED_KPI tests — which KPI is evaluated |
| `required_template_ids` | UUID[] | For DOCUMENT_UPLOAD tests — which document templates satisfy this test |
| `required_document_count` | INTEGER | Minimum number of approved documents needed (default 1) |
| `period_scope` | VARCHAR(20) | `CURRENT_SEMESTER`, `CURRENT_YEAR`, `ROLLING_3Y` — which documents are in scope |
| `is_required` | BOOLEAN | If false, test is optional (passing is good, failing doesn't block control) |
| `evaluation_logic` | JSONB | Flexible config for complex tests (e.g. threshold per benchmark band) |

---

### 2.4 Evidence

Evidence is the link between a test and the artifact that satisfies it. Evidence is created automatically when:
- An approved document's template is in `required_template_ids` for a DOCUMENT_UPLOAD test
- A KPI record meets the test threshold for an AUTOMATED_KPI test
- A staff member submits an attestation for an ATTESTATION test

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `test_id` | UUID | |
| `tenant_id` | UUID | |
| `evidence_type` | VARCHAR(20) | `DOCUMENT`, `KPI_RECORD`, `ATTESTATION` |
| `document_id` | UUID | FK to `documents.files` when evidence_type = DOCUMENT |
| `kpi_record_id` | UUID | FK to `kpi_records` when evidence_type = KPI_RECORD |
| `attestation_text` | TEXT | Submitted text when evidence_type = ATTESTATION |
| `attested_by` | UUID | User who submitted attestation |
| `is_active` | BOOLEAN | False when the source document is rejected or KPI record superseded |
| `linked_at` | TIMESTAMPTZ | When this evidence was auto-linked |

---

### 2.5 Control Status

The computed pass/fail state for a (control, institution, period) triple. Recomputed on:
- Any document approval or rejection
- Any KPI batch completion
- Any attestation submission or withdrawal

**Status values** (aligned with industry conventions):

| Status | Color | Meaning |
|---|---|---|
| `PASSING` | Green | All required tests pass; evidence is on file and approved |
| `FAILING` | Red | One or more required tests are failing; evidence missing or below threshold |
| `NEEDS_EVIDENCE` | Amber | Test is defined but no evidence has been submitted yet (pre-failing) |
| `NOT_APPLICABLE` | Grey | Control explicitly excluded with documented reason (e.g. survey-based QS indicators) |

> `NEEDS_EVIDENCE` is distinct from `FAILING`: a new institution that hasn't uploaded anything yet shouldn't appear red across the board — it hasn't failed, it hasn't started. This matches Vanta's "Needs Review" / Drata's "Needs Attention" concepts.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `tenant_id` | UUID | |
| `control_id` | UUID | |
| `status` | VARCHAR(20) | `PASSING`, `FAILING`, `NEEDS_EVIDENCE`, `NOT_APPLICABLE` |
| `passing_tests` | INTEGER | Count of passing tests for this control |
| `total_required_tests` | INTEGER | Total required (non-optional) tests |
| `failing_test_ids` | UUID[] | Tests that are currently failing |
| `missing_evidence` | JSONB | `{document_templates_needed: [{id, name}], kpi_inputs_needed: [{kpi_id, description}]}` |
| `not_applicable_reason` | TEXT | Populated when status = NOT_APPLICABLE |
| `waived_by` | UUID | User who marked NOT_APPLICABLE |
| `period_start` / `period_end` | DATE | Evaluation period |
| `evaluated_at` | TIMESTAMPTZ | |

---

## 3. Template → Control Linkage (The Core Mechanism)

Every document template in the system carries a list of test IDs it can satisfy. This is the bridge between the document ingestion pipeline and the accreditation engine.

```sql
-- Added to documents.templates table
ALTER TABLE documents.templates
  ADD COLUMN linked_test_ids UUID[];  -- tests this template satisfies when a document is approved
```

**How it works end-to-end:**

```
Admin defines Template: "Grade Sheet"
  → linked_test_ids = [test_id for ISO21001-8.2 document upload test,
                        test_id for ISO9001-8.1 document upload test]

Institution uploads a document → doc-service classifies it → matches "publication_list" template
  → Document enters review queue
  → Reviewer approves document
  → Approval event fires: accreditation-service notified
      → For each test_id in template.linked_test_ids:
          → Create Evidence record (evidence_type=DOCUMENT, document_id=...)
          → Re-evaluate the parent Control's status
          → Broadcast status update via WebSocket to any open Accreditation Dashboard
```

This means **every document approval is a compliance event**. The institution's accreditation posture improves automatically as their document portfolio grows — no manual tagging required after the template linkage is configured.

---

## 4. Template → Framework Control Mapping (Seed Data)

The following mappings are pre-configured at platform launch. Admins can add custom mappings.

| Template | Controls Satisfied |
|---|---|
| `grade_sheet` | ISO21001-8.2 (student performance monitoring), ISO9001-8.1 (operational control) |
| `syllabus` | ISO21001-8.3 (design of educational products), ISO9001-8.1 |
| `faculty_record` | ISO21001-7.1 (competence), ISO9001-7.2 (competence) |
| `hiring_dossier` | ISO21001-7.1 (competence), ISO9001-7.2 |
| `budget_report` | ISO21001-9.1 (monitoring & measurement), ISO9001-9.1 |
| `audit_report` | ISO21001-9.2 (internal audit), ISO9001-9.2 |
| `meeting_minutes` | ISO21001-9.3 (management review), ISO9001-9.3 |
| `risk_register` | ISO21001-6.1 (risk-based thinking), ISO9001-6.1 |
| `governance_charter` | ISO21001-4.4 (EOMS scope), ISO9001-4.3 (QMS scope) |
| `disaster_recovery_procedure` | ISO21001-8.5 (operational planning), ISO9001-8.1 |
| `energy_report` | GREENMETRIC-ENERGY (energy & climate change category) |
| `sustainability_survey` | GREENMETRIC-TRANSPORT (transport), GREENMETRIC-EDU (education & research) |
| `waste_report` | GREENMETRIC-WASTE (waste management category) |
| `water_report` | GREENMETRIC-WATER (water management category) |

---

## 5. Accreditation Dashboard — UI Specification

### 5.1 Framework Overview (landing)

Top-level view when a user opens the Accreditation section. Shows all active frameworks side by side.

```
┌──────────────────────────────────────────────────────────────┐
│  Accreditation & Framework Compliance                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  ISO 9001    │  │  ISO 21001   │  │  UI GreenMetric   │  │
│  │              │  │              │  │                   │  │
│  │  ████████    │  │  ██████░░    │  │  ████░░░░         │  │
│  │    8/10      │  │    8/12      │  │     4/6           │  │
│  │  PASSING     │  │  FAILING     │  │  FAILING          │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
│                                                              │
│  [Select framework to view details]                          │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Framework Detail View

Selected framework expanded. Two-panel layout: control list (left) + evidence portfolio (right, persistent).

**Control List (left panel)**

One row per control, sorted by: FAILING first, then NEEDS_EVIDENCE, then PASSING, then NOT_APPLICABLE. Within each group, sorted by weight descending.

```
┌──────────────────────────────────────────────────────────────────┐
│  ISO 21001:2018 — INSAT                      ████████░░ 8/12     │
├──────────────┬──────────────────────────┬────┬──────────┬────────┤
│  Code        │  Control                 │ W  │  Status  │ Evid.  │
├──────────────┼──────────────────────────┼────┼──────────┼────────┤
│ ISO21001-6.1 │ Risk register current    │ —  │ FAILING  │ 0 docs │
│ ISO21001-8.2 │ Student performance mon. │ —  │ PASSING  │ ✓ docs │
│ ISO21001-8.3 │ Syllabi on file          │ —  │ PASSING  │ ✓ docs │
│ ISO21001-9.2 │ Internal audit on sched. │ —  │ NEEDS_EV │ 0 docs │
│ ISO21001-9.3 │ Management review mins   │ —  │ PASSING  │ ✓ docs │
│ ...          │ ...                      │ …  │  ...     │  ...   │
└──────────────┴──────────────────────────┴────┴──────────┴────────┘
```

Clicking a row expands it inline to show:
- Official requirement description
- List of tests with individual pass/fail status
- For each failing test: exactly what evidence is needed (template name + link to upload)
- For passing tests: evidence on file (document name, upload date, link)
- "Mark as Not Applicable" button (requires reason, creates audit log entry)

### 5.3 Evidence Portfolio (right panel / tab)

All documents linked to at least one control in the currently selected framework. This is the document portfolio relevant to this accreditation — not all institution documents, only those with framework relevance.

```
┌─────────────────────────────────────────────────────────────────┐
│  Evidence Portfolio — ISO 21001:2018 · INSAT                    │
│                                                                 │
│  Showing 9 documents linked to ISO 21001 controls               │
│                                                                 │
│  [Search]  [Filter by: template | control | status]             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📄 grade_sheet_S1_2025.xlsx            Approved          │   │
│  │    Template: Grade Sheet                                 │   │
│  │    Uploaded: 2026-02-14  by: Admin INSAT                │   │
│  │    Satisfies: ISO21001-8.2 · ISO9001-8.1                │   │
│  │    [View document]  [View extraction]                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📄 audit_report_Q1_2026.pdf            Approved          │   │
│  │    Template: Internal Audit Report                       │   │
│  │    Uploaded: 2026-04-05  by: Quality Office             │   │
│  │    Satisfies: ISO21001-9.2 · ISO9001-9.2                │   │
│  │    [View document]  [View extraction]                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Missing evidence for failing/pending controls:                 │
│  ────────────────────────────────────────────────────────────  │
│  ⚠ ISO21001-6.1 needs: risk_register (0 approved on file)      │
│     [Upload risk register]                                      │
│  ⚠ ISO21001-9.2 needs audit_report updated within last 90 days  │
│     Last approved: 2025-12-10  — overdue                        │
│     [Upload new audit report]                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Gap Analysis Panel

Sorted action list: what to do next to improve framework compliance the most.

Each item = one failing or NEEDS_EVIDENCE test. Sorted by: `control_weight × (1 − current_progress)` descending — highest-impact gaps first.

```
Priority  Control            Gap                    Action required
────────  ─────────────────  ─────────────────────  ───────────────────────────────────
  1       ISO21001-6.1       0 docs on file          Upload risk register
          Risk register                              (affects 18 institutions)
  2       ISO21001-9.2       Last audit > 90 days    Upload Q1 2026 audit reports
          Internal audit     (11 institutions)       for overdue institutions
  3       GREENMETRIC-ENERGY KPI below threshold     Upload energy_report for
          Energy/student     (current: 85 kWh,       INSAT, IHEC, FSB (missing)
                             threshold: 60 kWh)
  4       ISO21001-7.1       3 institutions missing  Upload faculty records for
          Faculty records    hiring_dossier docs     Nabeul, Bizerte campuses
```

---

## 6. Data Schema

```sql
-- Frameworks
CREATE TABLE ucar_global.frameworks (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code            VARCHAR(20) UNIQUE NOT NULL,
  name_fr         VARCHAR(300) NOT NULL,
  name_ar         VARCHAR(300),
  version         VARCHAR(20),
  description     TEXT,
  scope           VARCHAR(20) CHECK (scope IN ('INSTITUTION', 'NETWORK')) DEFAULT 'INSTITUTION',
  is_active       BOOLEAN DEFAULT true
);

-- Controls within a framework
CREATE TABLE ucar_global.framework_controls (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  framework_id            UUID NOT NULL REFERENCES frameworks(id),
  code                    VARCHAR(30) NOT NULL,
  name_fr                 VARCHAR(300) NOT NULL,
  name_ar                 VARCHAR(300),
  description             TEXT,
  category                VARCHAR(100),
  weight                  NUMERIC(5,4) NOT NULL DEFAULT 0,
  passing_threshold       NUMERIC,
  warning_threshold       NUMERIC,
  unit                    VARCHAR(50),
  official_methodology    TEXT,
  requires_external_survey BOOLEAN DEFAULT false,
  not_applicable_reason   TEXT,
  owner_role              VARCHAR(50),
  UNIQUE (framework_id, code)
);

-- Tests that verify a control
CREATE TABLE ucar_global.control_tests (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  control_id              UUID NOT NULL REFERENCES framework_controls(id),
  name                    VARCHAR(300) NOT NULL,
  description             TEXT,
  test_type               VARCHAR(20) NOT NULL
                            CHECK (test_type IN ('AUTOMATED_KPI', 'DOCUMENT_UPLOAD', 'ATTESTATION')),
  kpi_id                  VARCHAR(10) REFERENCES kpi_definitions(kpi_id),
  required_template_ids   UUID[],          -- for DOCUMENT_UPLOAD tests
  required_document_count INTEGER DEFAULT 1,
  period_scope            VARCHAR(20) DEFAULT 'CURRENT_YEAR'
                            CHECK (period_scope IN ('CURRENT_SEMESTER', 'CURRENT_YEAR', 'ROLLING_3Y')),
  is_required             BOOLEAN DEFAULT true
);

-- Template → test linkage (denormalized for fast lookups on document approval)
-- This is the bridge: when a document of template T is approved, link it as evidence for all tests in this table
CREATE TABLE ucar_global.template_test_links (
  template_id   UUID NOT NULL REFERENCES documents.templates(id),
  test_id       UUID NOT NULL REFERENCES control_tests(id),
  PRIMARY KEY (template_id, test_id)
);

-- Evidence: approved artifacts linked to tests
CREATE TABLE ucar_global.control_evidence (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_id         UUID NOT NULL REFERENCES control_tests(id),
  tenant_id       UUID NOT NULL REFERENCES tenants(id),
  evidence_type   VARCHAR(20) NOT NULL CHECK (evidence_type IN ('DOCUMENT', 'KPI_RECORD', 'ATTESTATION')),
  document_id     UUID REFERENCES documents.files(id),
  kpi_record_id   UUID REFERENCES kpi_records(id),
  attestation_text TEXT,
  attested_by     UUID,
  is_active       BOOLEAN DEFAULT true,   -- false when source document rejected/superseded
  linked_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Live control status per institution
CREATE TABLE ucar_global.control_status (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL REFERENCES tenants(id),
  control_id            UUID NOT NULL REFERENCES framework_controls(id),
  status                VARCHAR(20) NOT NULL
                          CHECK (status IN ('PASSING','FAILING','NEEDS_EVIDENCE','NOT_APPLICABLE')),
  passing_tests         INTEGER DEFAULT 0,
  total_required_tests  INTEGER DEFAULT 0,
  failing_test_ids      UUID[],
  missing_evidence      JSONB,   -- {templates_needed: [{id,name}], kpi_inputs_needed: [{kpi_id,desc}]}
  not_applicable_reason TEXT,
  waived_by             UUID,
  waived_at             TIMESTAMPTZ,
  period_start          DATE,
  period_end            DATE,
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  evaluated_at          TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (tenant_id, control_id, period_start)
);
```

---

## 7. Evaluation Engine

The evaluation engine is triggered by three events:
1. Document approved (from `doc-service`)
2. KPI batch completed (from `kpi-service`)
3. Attestation submitted (from `accreditation-service` API)

```python
# Simplified evaluation flow (accreditation_service/engine/evaluator.py)

def evaluate_control(tenant_id: UUID, control_id: UUID, period: Period) -> ControlStatus:
    control = get_control(control_id)
    tests = get_required_tests(control_id)

    passing_tests = []
    failing_tests = []
    missing_evidence = {"templates_needed": [], "kpi_inputs_needed": []}

    for test in tests:
        if test.test_type == "AUTOMATED_KPI":
            kpi_record = get_latest_kpi_record(tenant_id, test.kpi_id, period)
            if kpi_record and kpi_record.value >= control.passing_threshold:
                passing_tests.append(test.id)
            else:
                failing_tests.append(test.id)
                if not kpi_record:
                    missing_evidence["kpi_inputs_needed"].append({
                        "kpi_id": test.kpi_id,
                        "description": f"No approved source documents for {test.kpi_id} in period"
                    })

        elif test.test_type == "DOCUMENT_UPLOAD":
            docs = get_approved_docs_for_templates(tenant_id, test.required_template_ids, period)
            if len(docs) >= test.required_document_count:
                passing_tests.append(test.id)
            else:
                failing_tests.append(test.id)
                missing_templates = [t for t in test.required_template_ids if not has_approved_doc(tenant_id, t, period)]
                missing_evidence["templates_needed"].extend(get_template_names(missing_templates))

        elif test.test_type == "ATTESTATION":
            attestation = get_active_attestation(tenant_id, test.id, period)
            if attestation:
                passing_tests.append(test.id)
            else:
                failing_tests.append(test.id)

    # Determine overall status
    if control.requires_external_survey and not any_evidence_exists(tenant_id, control_id, period):
        status = "NOT_APPLICABLE"
    elif not failing_tests and passing_tests:
        status = "PASSING"
    elif not any_evidence_exists(tenant_id, control_id, period):
        status = "NEEDS_EVIDENCE"
    else:
        status = "FAILING"

    return ControlStatus(
        tenant_id=tenant_id,
        control_id=control_id,
        status=status,
        passing_tests=len(passing_tests),
        total_required_tests=len(tests),
        failing_test_ids=failing_tests,
        missing_evidence=missing_evidence,
        period_start=period.start,
        period_end=period.end,
        evaluated_at=now()
    )
```

On document approval, the service:
1. Looks up `template_test_links` for the document's template
2. Creates `control_evidence` records for each linked test
3. Re-evaluates `control_status` for each affected control
4. Publishes status update events to Redis pub/sub → frontend WebSocket

---

## 8. API Endpoints

```
/accreditation/
  GET  /accreditation/frameworks/                         → List active frameworks
  GET  /accreditation/frameworks/{code}/controls/         → All controls for a framework
  GET  /accreditation/frameworks/{code}/status/           → Institution's control status for framework
  GET  /accreditation/frameworks/{code}/evidence/         → Evidence portfolio for framework (tenant-scoped)
  GET  /accreditation/frameworks/{code}/gaps/             → Gap analysis, sorted by impact
  GET  /accreditation/controls/{id}/                      → Control detail + tests
  GET  /accreditation/controls/{id}/evidence/             → Evidence on file for control
  POST /accreditation/controls/{id}/attest/               → Submit attestation for ATTESTATION tests
  POST /accreditation/controls/{id}/not-applicable/       → Mark NOT_APPLICABLE with reason
  DELETE /accreditation/controls/{id}/not-applicable/     → Reverse NOT_APPLICABLE
  GET  /accreditation/network/summary/                    → President view: all institutions × all frameworks (GLOBAL_READ)
  POST /accreditation/evaluate/trigger/                   → Manual re-evaluation trigger (admin)

/accreditation/templates/
  GET  /accreditation/templates/{template_id}/controls/   → Which controls this template satisfies
  POST /accreditation/templates/{template_id}/link/       → Link template to additional tests
  DELETE /accreditation/templates/{template_id}/link/{test_id}/ → Remove template-test link (blocked if active evidence exists; returns 409 with list of affected evidence records — caller must explicitly deactivate evidence first)
```

---

## 9. ISO 9001:2015 Control Mapping (Seed Data)

| Clause | Code | Control Name | Test Type | Templates |
|---|---|---|---|---|
| 4.3 | `ISO9001-4.3` | QMS scope defined | DOCUMENT_UPLOAD | `governance_charter` |
| 6.1 | `ISO9001-6.1` | Risk register current (≤30 days) | DOCUMENT_UPLOAD | `risk_register` |
| 7.2 | `ISO9001-7.2` | Staff competence records on file | DOCUMENT_UPLOAD | `faculty_record`, `hiring_dossier` |
| 7.5 | `ISO9001-7.5` | Document control compliance | AUTOMATED_KPI: GOV-01 | — |
| 8.1 | `ISO9001-8.1` | Operational planning — key procedures documented | DOCUMENT_UPLOAD | `syllabus`, `disaster_recovery_procedure` |
| 9.1 | `ISO9001-9.1` | Monitoring & measurement — performance data | DOCUMENT_UPLOAD | `budget_report`, `grade_sheet` |
| 9.2 | `ISO9001-9.2` | Internal audit completed on schedule | DOCUMENT_UPLOAD | `audit_report` |
| 9.3 | `ISO9001-9.3` | Management review meeting minutes | DOCUMENT_UPLOAD | `meeting_minutes` |
| 10.2 | `ISO9001-10.2` | Nonconformity closure rate | AUTOMATED_KPI: GOV-02 | `audit_report` |
| 10.3 | `ISO9001-10.3` | Continual improvement — evidence of action taken | ATTESTATION | — |

---

## 10. ISO 21001:2018 Control Mapping (Seed Data)

| Clause | Code | Control Name | Test Type | Templates |
|---|---|---|---|---|
| 4.1 | `ISO21001-4.1` | Context of the organization understood | ATTESTATION | — |
| 4.4 | `ISO21001-4.4` | EOMS scope defined and documented | DOCUMENT_UPLOAD | `governance_charter` |
| 6.1 | `ISO21001-6.1` | Risk register current (≤30 days) | DOCUMENT_UPLOAD | `risk_register` |
| 7.1 | `ISO21001-7.1` | Faculty competence records on file | DOCUMENT_UPLOAD | `faculty_record`, `hiring_dossier` |
| 7.2 | `ISO21001-7.2` | Training fulfillment rate ≥ 80% | AUTOMATED_KPI: HR-05 | — |
| 7.5 | `ISO21001-7.5` | Documented information control | AUTOMATED_KPI: GOV-01 | — |
| 8.2 | `ISO21001-8.2` | Student performance monitoring — grades documented | DOCUMENT_UPLOAD | `grade_sheet` |
| 8.3 | `ISO21001-8.3` | Curriculum design — syllabi on file | DOCUMENT_UPLOAD | `syllabus` |
| 8.5 | `ISO21001-8.5` | Operational planning — disaster recovery | DOCUMENT_UPLOAD | `disaster_recovery_procedure` |
| 9.1 | `ISO21001-9.1` | Monitoring & measurement — budget reports | DOCUMENT_UPLOAD | `budget_report` |
| 9.2 | `ISO21001-9.2` | Internal audit completed on schedule | DOCUMENT_UPLOAD | `audit_report` |
| 9.3 | `ISO21001-9.3` | Management review — meeting minutes | DOCUMENT_UPLOAD | `meeting_minutes` |

---

## 11. UI GreenMetric Control Mapping (Seed Data)

GreenMetric is NETWORK-scoped: the aggregate across all UCAR institutions is what's submitted. Each control has a quantitative threshold from the GreenMetric scoring rubric.

| Category | Code | Control | Test Type | KPI / Templates |
|---|---|---|---|---|
| Setting & Infrastructure | `GM-SI` | Green area ratio + open space on campus | DOCUMENT_UPLOAD + ATTESTATION | — |
| Energy & Climate Change | `GM-ENERGY` | Energy per student ≤ 60 kWh/student | AUTOMATED_KPI: ESG-01 + DOCUMENT_UPLOAD | `energy_report` |
| Waste | `GM-WASTE` | Recycling rate ≥ 50% | AUTOMATED_KPI: ESG-04 + DOCUMENT_UPLOAD | `waste_report` |
| Water | `GM-WATER` | Water conservation programs in place | DOCUMENT_UPLOAD | `water_report` |
| Transport | `GM-TRANSPORT` | Green transport rate ≥ 30% | AUTOMATED_KPI: ESG-05 + DOCUMENT_UPLOAD | `sustainability_survey` |
| Education & Research | `GM-EDU` | Sustainability courses + SDG-linked research | AUTOMATED_KPI: ESG-08 + DOCUMENT_UPLOAD | `sustainability_survey` |

---

## 12. Open Questions

| # | Question | Impact |
|---|---|---|
| Q1 | GreenMetric Setting & Infrastructure: how is green area ratio measured — self-reported or from campus map data? | GM-SI evidence type and template design |
| Q2 | ISO 9001 and ISO 21001 share many controls (6.1, 7.5, 9.2, 9.3) — should shared controls be deduplicated into one test or maintained separately per framework? | DB design: shared `control_evidence` rows vs. duplicated |
| Q3 | Network-scoped GreenMetric controls: `tenant_id = NULL` for aggregate status row — confirm this is the intended query pattern | Affects President view dashboard queries |
