"""FastAPI dependencies for the KPI service.

`get_current_tenant_id` reads `X-Tenant-Id` from the request header for
now. Once Keycloak/JWT is wired the same dep will extract the tenant
claim from the verified access token; the call sites stay unchanged.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.session import get_session


async def get_current_tenant_id(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> UUID:
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Id header is required",
        )
    try:
        return UUID(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Id must be a valid UUID",
        ) from exc


SessionDep = Annotated[AsyncSession, Depends(get_session)]
TenantDep = Annotated[UUID, Depends(get_current_tenant_id)]
