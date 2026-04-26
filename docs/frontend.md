# Frontend

**Path:** [FrontEnd/](../FrontEnd/)
**Stack:** React 18 + TypeScript + Vite + Tailwind CSS v4 + Zustand + Recharts + Framer Motion

## Why these choices

- **Vite over Next.js / CRA** — instant HMR (sub-100 ms), tiny config, dev proxy out of the box. We have no SEO requirement (this is an authenticated ERP), so SSR buys nothing.
- **Zustand over Redux** — single-store global state without the boilerplate. The app's global state is essentially `{user, currentInstitution, notifications}`; Redux Toolkit would be a tax.
- **Tailwind v4 with Vite plugin** — the new engine; no `tailwind.config.js`, theme tokens live in CSS. Fast.
- **Recharts for charts** — declarative React-style; covers the bar/line/radar/sparkline cases the dashboard needs.
- **Framer Motion** — the page transitions between Overview ↔ Institution Detail use shared-element-style animations.
- **react-simple-maps** — Tunisia choropleth on the Overview page.

## Routes — [App.tsx](../FrontEnd/src/App.tsx)

| Path | Page | Audience |
|---|---|---|
| `/` | `Overview` | Everyone — network-wide KPI snapshot, map, top-line numbers |
| `/institutions` | `Institutions` | Analysts — list with filter/sort by KPI |
| `/institutions/:code` | `InstitutionDetail` | Analysts + directors — drill-down by domain |
| `/rankings` | `Rankings` | Network-wide ranked tables, predictor band view |
| `/alertes` | `Alerts` | Analysts — KPI threshold breaches, late submissions |
| `/reports` | `Analytics` | Analysts — comparative analytics across periods |
| `/finance` | `Finance` | Directors — Domain E (finance) cockpit |
| `/accreditations` | `Accreditations` | Directors — ISO 9001 / 21001 / GreenMetric control status |
| `/professors` | `Professors` | HR — faculty directory with OpenAlex enrichment status |
| `/ingestion` | `Ingestion` | All upload roles — the full pipeline UI |

`AppShell` (in [components/layout/AppShell.tsx](../FrontEnd/src/components/layout/AppShell.tsx)) wraps all of these; provides the sidebar, topbar, and toast container.

## The Ingestion page — the most important screen

[pages/Ingestion.tsx](../FrontEnd/src/pages/Ingestion.tsx) is the demo's centerpiece. State flow:

```
1. User picks domain + period + drops file
       │
       ▼
   POST /upload   →   import_id returned, status="pending"
       │
       ▼
2. Page polls GET /imports/{id}/status every 2s
       │
       ▼
   status="extracted"  →  show extracted_headers as chips, show preview rows
       │                  show templates_matcher result (auto-confirm badge or suggestion)
       ▼
3. If no auto-confirm: user maps columns to fields, optionally saves as template
       │
       ▼
   POST /imports/{id}/confirm-mapping
       │
       ▼
4. status="mapping_confirmed" → status="validated"
       │  validation_summary shows records_valid / records_warned / records_quarantined
       ▼
5. User clicks "Engager les données"  →  POST /imports/{id}/commit
       │
       ▼
   status="committed"  →  toast success, redirect to dashboard
```

The polling logic + state-derived UI is the demo's hardest piece, and it's also the one that proves the async pipeline works. **Every status transition the user sees corresponds to a Celery task completion writing to `import_records`.**

## API client — [lib/api.ts](../FrontEnd/src/lib/api.ts)

Single fetch wrapper, base URL configured by Vite proxy in dev (`/api/ingestion → http://localhost:8010`, `/api/kpi → http://localhost:8002`). In production this becomes nginx upstream rules to the same services. No bespoke client per service — typed wrappers per endpoint, that's it.

## State store — [store.ts](../FrontEnd/src/store.ts)

Zustand store with three slices:

- `user` — current user object decoded from JWT (or the local-mode fake)
- `notifications` — toast queue
- `selectedInstitution` — the cross-page selected institution (used by Overview → Institution Detail navigation)

Page-local state stays in `useState`. Server data stays in fetch-derived cache (no SWR/TanStack Query in this build — the dashboard's read patterns are simple enough that hand-rolled effects are fine; we'd add TanStack Query the moment polling becomes more than a single page).

## Type sharing

There is **no shared type package** between backend and frontend. Pydantic schemas on the backend, `types.ts` on the frontend, manually kept in sync. With ~10 endpoints this is cheaper than wiring openapi-typescript or `datamodel-code-generator`. The moment we add a 30th endpoint or add a non-React client, that calculus flips.

## Internationalization

**French-only**, hardcoded. Tunisian higher-education users are uniformly French-literate, and the deadline didn't justify wiring i18next. All copy lives inline in the components. Domain labels and KPI names come from the backend in French.

## What you'll be asked

- *"Why React and not Vue / Svelte?"* — team familiarity, ecosystem (Recharts, react-simple-maps, Tailwind plugins). Svelte would be smaller and faster; React is what we ship faster *with*.
- *"How do you handle slow extractions in the UI?"* — the polling loop shows the current `status` as a labeled badge ("Extraction en cours...", "Mapping proposé", etc.). The user is never staring at an unchanging spinner.
- *"What about offline / spotty network?"* — out of scope for a back-office ERP. Users are on wired institution networks. If the upload's POST fails we surface the error and let them retry; the import_record only exists if the POST succeeded.
- *"Why client-side polling instead of WebSockets / SSE?"* — polling is simpler, has no proxy/load-balancer pitfalls, and the granularity (2s) is fine for human-perceived latency. SSE is a 30-minute upgrade if needed; the API state machine doesn't change.
- *"How would you scale this UI to 50 institutions × 5 years × 8 domains?"* — pagination + virtualization on the institution list, lazy-loaded charts, server-side aggregation for the Overview map. The Recharts components are already set up to consume already-aggregated payloads from the KPI service.
