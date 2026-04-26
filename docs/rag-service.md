# RAG Service

**Path:** [backend/services/rag_service/](../backend/services/rag_service/)
**Port:** 8020 (planned)
**Status:** 🟡 **Scaffold only** — file structure, types, and route signatures are in place; every function body raises `NotImplementedError`.

## Why it exists

Once data is ingested and KPIs computed, users want to **ask questions** in natural language: *"why is INSAT's research domain trailing ENIT this period?"*, *"what does ISO 21001 require for risk planning?"*, *"which institutions are missing the 2026-S1 finance template?"*. A RAG (retrieval-augmented generation) layer is the right shape for this: pull the relevant rows + framework text + audit history, ground the LLM on them, return an answer with citations.

The scaffold is in the repo so the **interface is decided** and the **next session can implement bodies without re-debating shape**.

## Logical pipeline

```
question
   │
   ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  embed Q    │ → │ vector      │ → │ rerank      │ → │ build prompt│ → │ generate    │
│             │   │ search      │   │ (optional)  │   │ + citations │   │ (Claude)    │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
                  filter by             cross-encoder      system+user
                  institution_id        on top-K           prompt template
                  + sources
```

## Sources to index (planned)

| Source name | What it is | Chunk strategy |
|---|---|---|
| `data_records` | Committed KPI rows | One chunk per `(institution, period, domain)` bundle |
| `accreditation_frameworks` | ISO 9001 / 21001 / GreenMetric controls and tests | One chunk per control |
| `uploaded_documents` | Raw text from PDFs/Excel sheets in `uploads/` | Token-window with overlap |
| `prompt_templates` | The `prompts/` folder itself | One chunk per template file |

The chunking strategies live in [domain/chunker.py](../backend/services/rag_service/domain/chunker.py) as separate functions per source type — different sources need different granularity, and the indexer dispatches on source name.

## Stack choices (declared in [config.py](../backend/services/rag_service/config.py))

- **Embedding model:** `intfloat/multilingual-e5-large` (1024-dim). Already used by the ingestion service for column mapping — same model means a single warm cache in production.
- **Vector store:** `pgvector` on the same Postgres the rest of the system uses. We avoid adding a Pinecone/Qdrant ops surface for the demo's sake.
- **Generation model:** `claude-opus-4-7` (the SDK is already in `pyproject.toml`).
- **Top-K:** 6 by default, configurable per query.
- **Min score:** 0.25 (cosine similarity floor).

## Why scaffold and not implementation?

Three reasons, in priority order:

1. **The dependencies are already in place** (`sentence-transformers`, `anthropic`) — there's nothing to install. But the embedding step needs ~1.5 GB of model weights to download on first run, and that download is not something we want to debug live in a demo.
2. **The retrieval target needs real data first.** Indexing makes sense after `data_records` has rows; in the current demo state we have a few seeded institutions and that's it.
3. **The interface is the load-bearing part.** Pydantic schemas in [schemas/__init__.py](../backend/services/rag_service/schemas/__init__.py) define `QueryRequest` (with `institution_id` for RBAC, `top_k`, `sources`) and `QueryResponse` (with `Citation` objects carrying `source`, `chunk_id`, `score`, `snippet`). Once that contract is fixed, the implementation is mechanical.

## File-by-file

| File | Purpose |
|---|---|
| `main.py` | FastAPI app factory; mounts the router |
| `config.py` | `RAG_*` env-prefixed `BaseSettings`; embedding model, vector backend, top_k, etc. |
| `api/routes.py` | `/rag/health`, `/rag/sources`, `/rag/index`, `/rag/query` |
| `schemas/__init__.py` | Request and response Pydantic models, `Citation` |
| `domain/chunker.py` | `chunk_text`, `chunk_data_records`, `chunk_framework` |
| `domain/indexer.py` | `index_source`, `embed_chunks`, `upsert_chunks`, `delete_by_institution` |
| `domain/retriever.py` | `retrieve` (vector search) + `rerank` (cross-encoder) |
| `domain/generator.py` | `build_prompt`, `generate` (Anthropic call) |
| `repositories/__init__.py` | `VectorRepository` Protocol — pgvector / faiss / inmemory backends behind one interface |
| `prompts/rag/system_prompt.md` | French-first system prompt template with `{context}` and `{question}` placeholders |

## RBAC and tenancy

`QueryRequest.institution_id` is the hook. The retriever is expected to filter chunks by institution before vector search:

- A `super_admin` or `ucar_analyst` may query without `institution_id` (cross-network retrieval).
- An `institution_director` or `institution_admin` is constrained to their own institution by [shared/auth/dependencies.py](../backend/shared/auth/dependencies.py) before the request even reaches the retriever.

`delete_by_institution()` exists on the indexer for the same reason: when an institution leaves the system, its embeddings must go too.

## What you'll be asked

- *"Why didn't you implement it?"* — see the three reasons above. The scaffold makes the design explicit; building bodies without first pinning the interface is the more expensive path.
- *"Why pgvector and not a dedicated vector DB?"* — we already run Postgres. Adding a second stateful service for the prototype is operational debt with no benefit at this scale (low millions of chunks max).
- *"Why `intfloat/multilingual-e5-large`?"* — French + Arabic content is on the menu (Tunisian university docs are bilingual). e5-large outperforms `all-MiniLM` and `mpnet` on multilingual benchmarks, and 1024 dims is fine on pgvector with an HNSW index.
- *"How do you stop hallucination?"* — the system prompt at [prompts/rag/system_prompt.md](../prompts/rag/system_prompt.md) explicitly forbids inventing facts, mandates `[source:chunk_id]` citations, and instructs the model to refuse in French if the context doesn't answer. Citations let the user verify each claim against the chunk it came from.
