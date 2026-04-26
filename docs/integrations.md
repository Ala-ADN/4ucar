# External integrations

**Path:** [backend/integrations/](../backend/integrations/) and [backend/services/ingestion_service/mapping/](../backend/services/ingestion_service/mapping/)

## Philosophy: enrichment, not blocking

Every external API in this system is **non-blocking**. If OpenAlex is down, professor enrichment runs partially and resumes later. If Anthropic is down, mapping falls back to local fuzzy matching. If Gemini's quota is exhausted, same fallback. **The hot path of the application — upload → extract → commit — never depends on a remote API.** This is the data-sovereignty story we tell the jury.

## OpenAlex — [integrations/openalex.py](../backend/integrations/openalex.py)

**Primary research-data provider.** OpenAlex is a free, open scholarly database derived from Crossref, ORCID, ROR and the retired MAG.

- No API key. Providing an email in the `User-Agent` opts into the "polite pool" with a 10 req/s sustained limit.
- Returns: works, authors, institutions, citations, open-access status.

What it fills:

| OpenAlex field | KPI fed |
|---|---|
| `works.open_access.is_oa` | RES-11 (open-access share) |
| `authorships[*].countries` | RES-04 (international co-authorship) |
| `works.cited_by_percentile_year` | RES-09 (top-1% citations proxy) |
| `author.summary_stats.h_index` | RES-02 (h-index) |
| `author.cited_by_count`, `author.works_count` | RES-01, RES-03 |

Reference: https://docs.openalex.org/

The script [scripts/enrich_professors_openalex.py](../scripts/enrich_professors_openalex.py) does a one-shot enrichment for an institution. Long-term this becomes a Celery beat job — refresh once a quarter is plenty for citation data.

## Google Scholar — [integrations/google_scholar.py](../backend/integrations/google_scholar.py)

Used as a **fallback** for authors not indexed in OpenAlex (older Tunisian-language publications, conference papers without DOIs). Implementation uses the `scholarly` library, which scrapes the Scholar HTML and is fragile by design — Google rate-limits aggressively and rotates anti-bot challenges.

Always tried *after* OpenAlex; only the gaps go to Scholar. This minimizes exposure to Scholar's instability while still capturing tail data.

## Anthropic Claude — [services/ingestion_service/mapping/claude_mapper.py](../backend/services/ingestion_service/mapping/claude_mapper.py)

Column-to-KPI-field mapping proposer. Sent: list of headers + the domain's field catalog (id + label + aliases). Returned: JSON proposal `[{column, field_id, confidence, reason}]`.

Used for:

- Mapping suggestions on first upload of a new template (before any saved `DocumentTemplate` exists).

Settings: `CLAUDE_TIMEOUT_SECONDS=15`, `CLAUDE_MAX_RETRIES=2`, both env-driven via the ingestion service's [config.py](../backend/services/ingestion_service/config.py). On any failure the call falls through to `fuzzy_mapper.py`.

## Google Gemini — [services/ingestion_service/mapping/gemini_mapper.py](../backend/services/ingestion_service/mapping/gemini_mapper.py)

Same role as Claude, alternative implementation. The current build's default mapper. The choice is one config flip; either model can produce the same JSON shape.

## Fuzzy fallback — [mapping/fuzzy_mapper.py](../backend/services/ingestion_service/mapping/fuzzy_mapper.py)

Pure Python `difflib.get_close_matches` over an alias map built from `kpi_schema.py`. Cutoff 0.6. **No external calls, fully data-sovereign**, lower quality than the LLM proposals but always available.

Order of operations in the mapping stage:

```
saved template? ── yes ──► auto-confirm if Jaccard ≥ 0.6, else show as suggestion
       │
       no
       ▼
LLM mapper (Gemini default) ── failure ──► fuzzy fallback
       │                                          │
       └──────► mapping_proposal written ◄────────┘
```

## Keycloak — [shared/auth/](../backend/shared/auth/)

OIDC identity provider for production. See [auth-and-rbac.md](auth-and-rbac.md). Configured in `.env`, integration through `httpx` against the realm's discovery endpoints. Bypassed when `APP_ENV=local`.

## Sentry — declared in `pyproject.toml`

`sentry-sdk` is in the dependency tree for production error tracking. Not initialized in the prototype to keep noise out of demo logs.

## Prometheus — declared in `pyproject.toml`

`prometheus-fastapi-instrumentator` is in the dependency tree, ready to mount on `/metrics`. Not enabled in the prototype.

## What you'll be asked

- *"What's your data sovereignty story?"* — OCR runs locally (PaddleOCR), embeddings run locally (`multilingual-e5-large`), mapping has a fully local fuzzy fallback. The only external API in the *hot path* of ingestion is the optional LLM mapper, and it's optional. The KPI computation never calls out at all.
- *"Why two LLM providers?"* — risk diversification. If one API has an outage during the demo, we flip a config and use the other. Both share the same JSON output contract.
- *"What if OpenAlex changes its schema?"* — the integration is a thin adapter (`integrations/openalex.py`) that maps response fields to typed dataclasses (`FacultyMember`, `Publication`). A schema change is a one-file fix; nothing else in the system knows about OpenAlex's shape.
- *"How do you handle rate limits?"* — `tenacity` (in `pyproject.toml`) gives us decorator-based retry with exponential backoff. For OpenAlex we throttle at 10 req/s; for Scholar we let `scholarly` handle backoff but cap concurrent runs to one Celery worker slot. Anthropic and Gemini are bounded by `CLAUDE_TIMEOUT_SECONDS` and the `max_retries` setting.
- *"Are you sending student data to OpenAI/Anthropic?"* — no. The mappers receive **column headers** (e.g. "Nombre d'inscrits 2026-S1"), not row data. The cell values never leave Postgres.
