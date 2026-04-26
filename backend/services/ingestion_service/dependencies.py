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
    async for session in get_session():
        yield session


# Hard-coded dev identity. Used only when APP_ENV=local and no
# Authorization header is provided — gives the portal a working session
# while Keycloak/JWT issuance is still being wired. Production will reject
# unauthenticated requests as before.
_DEV_USER = CurrentUser(
    user_id=uuid.UUID("00000000-0000-0000-0000-0000000000aa"),
    institution_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    role=Role.SUPER_ADMIN,
)


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    settings = get_settings()
    if not authorization or not authorization.startswith("Bearer "):
        if settings.app_env == "local":
            return _DEV_USER
        raise SessionExpired(detail="Authorization header missing or malformed.")

    token = authorization.removeprefix("Bearer ").strip()

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
