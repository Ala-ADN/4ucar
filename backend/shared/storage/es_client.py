"""Elasticsearch client: per-tenant `docs-{code}` index for full-text + vector search."""


def get_es_client():
    raise NotImplementedError


def tenant_index(institution_code: str) -> str:
    raise NotImplementedError
