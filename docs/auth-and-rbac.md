# Authentication & RBAC

**Path:** [backend/shared/auth/](../backend/shared/auth/) and [backend/services/ingestion_service/dependencies.py](../backend/services/ingestion_service/dependencies.py)

## Identity provider

**Production target:** Keycloak (already configured in `.env` with realm `ucar`, client `ucar-backend`). Tokens are JWTs signed by Keycloak; the API verifies signatures using the realm's JWKS.

**Prototype today:** when `APP_ENV=local` the JWT verification is bypassed and a fake user (`role=super_admin`) is injected by [`dependencies.py`](../backend/services/ingestion_service/dependencies.py). This is what the demo runbook uses. **In production this code path is dead** — `APP_ENV=production` forces real JWT validation through [`shared/auth/jwt.py`](../backend/shared/auth/jwt.py).

The `python-keycloak` package was previously in `pyproject.toml` and was removed because of network timeouts during install. The integration code uses raw `httpx` against Keycloak's OIDC discovery endpoints, so the package isn't strictly required.

## Roles

The full role list lives in [shared/auth/rbac.py](../backend/shared/auth/rbac.py); the **ingestion + KPI services use a 4-role subset**:

| Role | Scope | What they can do |
|---|---|---|
| `super_admin` | All institutions | Everything, including unlock periods, purge files, manage users |
| `ucar_analyst` | All institutions | Upload + approve + import historical + override quarantine + rollback + audit log |
| `institution_director` | Their own institution | Upload + approve + export reports, **no historical / no override** |
| `institution_admin` | Their own institution | Upload only |

Legacy roles from the original master spec (`student`, `faculty`, `dean`, `president`, `mesrs_auditor`, etc.) still have permission entries for forward-compatibility but no service uses them in this build.

## Permissions

`Permission` is a `StrEnum` with one value per privileged action. Per-role allowlists are static dictionaries in `_ROLE_PERMISSIONS`. Three functions:

```python
role_permissions(role: Role) -> set[Permission]
check_permission(role: Role, permission: Permission) -> bool
require(role: Role, permission: Permission) -> None    # raises PermissionDenied
```

`require()` is the one called in routers. Failed checks raise `PermissionDenied`, which the global handler in [`shared/exceptions.py`](../backend/shared/exceptions.py) converts to HTTP 403 with a French message body.

### Notable permissions

| Permission | What it gates |
|---|---|
| `UPLOAD_DOCUMENTS` | `POST /upload` |
| `IMPORT_HISTORICAL` | `is_historical=True` flag — only super_admin and ucar_analyst |
| `APPROVE_EXTRACTIONS` | `POST /imports/{id}/confirm-mapping`, `POST /imports/{id}/commit` |
| `OVERRIDE_QUARANTINE` | Resolving a quarantine row with `resolution=override` |
| `ROLLBACK_IMPORT` | `POST /imports/{id}/rollback` (within `ROLLBACK_WINDOW_DAYS`) |
| `UNLOCK_PERIOD` | Removing a `LockedPeriod` row |
| `VIEW_AUDIT_LOG` | `GET /audit` |
| `PURGE_FILES` | Hard delete of `data_records` and uploaded files |
| `MANAGE_DATA_REQUESTS` | Creating UCAR-central data requests |
| `EXPORT_MESRS_REPORT` | Generating MESRS-format PDF reports |

## Tenancy enforcement

The RBAC matrix doesn't know which institution a user belongs to — that's a *tenancy* check on top of permissions. Pattern:

```python
from backend.services.ingestion_service.dependencies import require_own_institution
from backend.shared.auth.rbac import require, Permission

async def some_endpoint(institution_id: UUID, current_user: CurrentUser, ...):
    require(current_user.role, Permission.UPLOAD_DOCUMENTS)
    require_own_institution(institution_id, current_user)
    # ... proceed
```

`require_own_institution()` is a no-op for `super_admin` and `ucar_analyst` (they're cross-institution), and a hard 403 for institution-scoped roles when `current_user.institution_id != institution_id`.

The longer-term plan is **row-level security** at the Postgres layer: every connection sets a session GUC `app.current_institution_id`, and every tenant table has an RLS policy `USING (institution_id = current_setting('app.current_institution_id')::uuid)`. The scaffold for this is in [shared/db/rls.py](../backend/shared/db/rls.py) and [shared/tenancy/middleware.py](../backend/shared/tenancy/middleware.py); it's not active because debugging RLS during a hackathon is a poor use of time.

## What you'll be asked

- *"How do you authenticate the frontend?"* — Vite dev mode runs with `APP_ENV=local` and skips auth. In production, the React app does an OIDC code flow against Keycloak, gets a bearer token, and sends it as `Authorization: Bearer ...`. The API verifies via JWKS.
- *"Why not OAuth2 from scratch?"* — Keycloak gives us SSO, MFA, password policies, audit logging, and a Tunisia-friendly admin UI for free. Reinventing it is unjustified.
- *"What happens when a user changes role?"* — Keycloak issues a new token at next login; existing tokens (15-min default lifetime in `realm.json`) continue with the old role until expiry. Refresh tokens are revoked on role change.
- *"Where do you check permissions — middleware or per-handler?"* — per-handler. Middleware can enforce *authentication* (token present and valid), but *authorization* (which permission for which action) belongs next to the action it gates so it's auditable from a code review of the handler.
- *"How does an institution_admin avoid leaking data?"* — three layers: JWT carries `institution_id`, `require_own_institution()` rejects mismatches, and **eventually** RLS makes mismatches impossible to express even from a misbehaving query.
