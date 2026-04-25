"""Row-level security: set `app.current_tenant` GUC at session start.

See master spec section 12.2 — every query is implicitly filtered by the
PostgreSQL RLS policy `tenant_isolation`.
"""


async def apply_tenant_guc(session, tenant_id) -> None:
    raise NotImplementedError
