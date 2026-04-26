"""FastAPI dependency factories for the ingestion service.

Single location for all auth + DB dependencies — no duplication per endpoint.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ingestion_service.config import get_settings
from backend.shared.auth.jwt import decode_token
from backend.shared.auth.rbac import Permission, Role, require
from backend.shared.db.session import get_session
from backend.shared.exceptions import PermissionDenied, SessionExpired, TenantScopeViolation


@dataclass
class CurrentUser:
    user_id: uuid.UUID
    institution_id: uuid.UUID
    role: Role


async def get_db() -> AsyncSession:
    settings = get_settings()
    async for session in get_session(settings):
        yield session


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise SessionExpired(detail="Authorization header missing or malformed.")

    token = authorization.removeprefix("Bearer ").strip()
    settings = get_settings()

    claims = decode_token(token, settings.app_secret_key)

    try:
        user_id = uuid.UUID(claims["sub"])
        institution_id = uuid.UUID(claims["institution_id"])
        role = Role(claims["role"])
    except (KeyError, ValueError) as exc:
        raise SessionExpired(detail=f"Invalid token claims: {exc}") from exc

    return CurrentUser(user_id=user_id, institution_id=institution_id, role=role)


def require_role(*permissions: Permission):
    """Dependency factory: raises PermissionDenied if the user lacks any of the given permissions."""

    async def _dep(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        for perm in permissions:
            require(current_user.role, perm)
        return current_user

    return _dep


def require_own_institution(institution_id: uuid.UUID, current_user: CurrentUser) -> None:
    """Raise TenantScopeViolation if the user is scoped to a different institution."""
    is_global = current_user.role in (Role.SUPER_ADMIN, Role.UCAR_ANALYST, Role.IT_ADMIN)
    if not is_global and current_user.institution_id != institution_id:
        raise TenantScopeViolation(
            detail=f"User institution {current_user.institution_id} != requested {institution_id}"
        )
