"""Per-request tenant context bound to a contextvar."""

from contextvars import ContextVar
from uuid import UUID

current_tenant_id: ContextVar[UUID | None] = ContextVar("current_tenant_id", default=None)


def set_tenant(tenant_id: UUID) -> None:
    raise NotImplementedError


def require_tenant() -> UUID:
    raise NotImplementedError
