"""Retrieval-augmented generation over the per-tenant Elasticsearch index."""


async def retrieve(query: str, tenant_id, top_k: int = 8):
    raise NotImplementedError


async def synthesize(query: str, passages):
    raise NotImplementedError
