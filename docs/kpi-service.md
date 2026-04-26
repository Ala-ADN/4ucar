# KPI Service

**Path:** [backend/services/kpi_service/](../backend/services/kpi_service/)
**Port:** 8002
**Purpose:** compute domain-specific indicators from `data_records`, expose them through HTTP, evaluate accreditation compliance.

## The eight domains

The KPI catalog is split by responsibility, mirroring the Tunisian MESRS reporting structure. Each domain lives in its own module under [domain/](../backend/services/kpi_service/domain/) and exposes a list of pure-function calculators.

| Domain | Module | Responsibility |
|---|---|---|
| A — Research & citations | `research.py` | Publications per faculty, h-index, OA share, top-1% citations, international co-authorship |
| B — Academic quality & teaching | `academic.py` | Pass rates, retention, student/teacher ratio, course evaluations |
| C — Employment & alumni | `employment.py` | Employment rate at 6/12/24 months, salary medians, time-to-first-job |
| D — Internationalization | `international.py` | Inbound/outbound mobility, joint diplomas, foreign faculty share |
| E — Finance | `finance.py` | Revenue per student, research grant intake, sponsored research share |
| F — HR | `hr.py` | Faculty pyramid, age structure, tenure rate, gender balance |
| G — Sustainability | `sustainability.py` | UI GreenMetric components: setting, energy, waste, water, transport, education |
| H — Accreditation | `accreditation.py` | ISO 9001, ISO 21001, UI GreenMetric — qualitative compliance, not a number |

## The calculator contract — [domain/result.py](../backend/services/kpi_service/domain/result.py)

Every calculator A through G has the same shape:

```python
def calc_xxx(inputs: InstitutionXxxInputs) -> KpiResult: ...
```

- Pure function. No I/O, no DB, no global state.
- Input is a typed dataclass from [`inputs.py`](../backend/services/kpi_service/domain/inputs.py).
- Output is a `KpiResult(kpi_id, value, status, details)`.

This is what makes the KPI engine **fully unit-testable** with hand-built fixtures. The repository's tests under [tests/unit/test_domain_*_kpis.py](../tests/unit/) hit each calculator with synthetic inputs and assert exact numeric output. No mocks needed because there is nothing to mock.

The dispatcher in [`computation.py`](../backend/services/kpi_service/domain/computation.py) just runs every calculator in a domain's `DOMAIN_X_CALCULATORS` list against the inputs and returns the list of results. Adding a new KPI is one file edit + one entry in the calculator list.

## Domain H — accreditation (the qualitative one)

Domain H does **not** return numbers. It returns `ControlEvaluation` per control:

```python
ControlStatus = PASSING | FAILING | NEEDS_EVIDENCE | NOT_APPLICABLE
```

The model is borrowed from the Vanta/Drata SaaS compliance world: **framework → control → test → evidence**.

Three frameworks are seeded in [`frameworks.py`](../backend/services/kpi_service/domain/frameworks.py):

- **ISO 9001:2015** — Quality Management (10 controls)
- **ISO 21001:2018** — Educational Organizations Management (8 controls)
- **UI GreenMetric** — Sustainability ranking (6 categories)

Each control has tests of three types:

- `AUTOMATED_KPI` — references a kpi_id from Domains A–G; passes when `inputs.kpi_values[kpi_id]` satisfies a threshold (`>=`, `<=`, `>`, `<`, `==`)
- `DOCUMENT_UPLOAD` — references a `template_code`; passes when an `ApprovedDocument` with that code is on file and not expired
- `ATTESTATION` — passes when a matching attestation exists in `inputs.attestations`

Status decision tree (from [`accreditation.py`](../backend/services/kpi_service/domain/accreditation.py)):

```
1. Waived for this control                  → NOT_APPLICABLE
2. requires_external_survey AND no evidence → NOT_APPLICABLE
3. all required tests pass                  → PASSING
4. no evidence of any kind exists yet       → NEEDS_EVIDENCE
5. otherwise                                → FAILING
```

This separation between "we tried but failed" (FAILING) and "you haven't started" (NEEDS_EVIDENCE) is what an actual auditor wants to see.

## Recompute pipeline — [services/recompute.py](../backend/services/kpi_service/services/recompute.py)

Triggered two ways:

1. **Event-driven** — subscribed to Redis channel `data.events`; when a `data.committed` message arrives for `(institution_id, period, domain)`, only that slice is recomputed.
2. **On-demand** — `POST /kpi/recompute` (gated by `Permission.TRIGGER_KPI_RECOMPUTE`) recomputes a full institution-period.

Recompute reads `data_records` for the slice, builds the typed `InstitutionXxxInputs`, runs the calculators, upserts `kpi_records`. Domain H additionally pulls `ApprovedDocument`s and `Attestation`s and emits `ControlEvaluation`s into a separate table.

## Predictor — [domain/predictor.py](../backend/services/kpi_service/domain/predictor.py)

Stub for international ranking band prediction (e.g., QS band). Plan: Ridge regression on past KPI vectors, with **SHAP** for per-feature attribution so we can show the institution *which* KPI changes would move them up a band. SHAP is in `pyproject.toml`; the model is not trained yet — we have no labeled historical band data in this scaffold. **The interface is in place; the model is the next session's work.**

## Routes

| Route | Purpose |
|---|---|
| `GET /kpi/catalog` | Static metadata for every KPI (id, label, domain, unit, target) |
| `GET /kpi/{institution_id}/{period}` | Computed KPI values for one slice |
| `POST /kpi/recompute` | Manual recompute trigger |
| `GET /accreditations/{institution_id}/{framework_code}` | Per-control evaluation results |
| `GET /professors/{institution_id}` | Faculty list, optionally enriched from OpenAlex |
| `POST /professors/{institution_id}/enrich` | Trigger OpenAlex/Scholar enrichment |

## Why no Celery tasks here?

Recompute is fast enough to run inline (single-domain on one institution is sub-second on real data). If a network-wide recompute (~50 institutions × 8 domains × 2 periods) becomes a bottleneck, moving it to Celery is a 30-minute change — the dispatcher already takes typed inputs, so the worker just needs to load them from Postgres and call `compute_*_domain`.

## What you'll be asked

- *"Where do KPI thresholds come from?"* — they are part of the framework definition (`FrameworkControl.tests[*].threshold`). For Domains A–G, the **target** comes from `kpi_catalog`; for Domain H, the **threshold** is encoded in the test definition. Both are reference data, code-versioned, not user-editable from the UI in this build.
- *"What if input data is missing?"* — `KpiResult.status` carries `INSUFFICIENT_DATA`; calculators always return a result, never throw. Domain H's `NEEDS_EVIDENCE` plays the same role.
- *"How do you avoid recomputing everything when one row changes?"* — `data.committed` payload contains `(institution_id, period, domain)`. Only that triple is recomputed.
- *"Why is accreditation separate from the numeric domains?"* — different output type, different consumers. Numeric KPIs feed dashboards and rankings; accreditation feeds the formal MESRS audit report and the Vanta-style compliance dashboard.
