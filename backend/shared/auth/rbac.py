"""Role-based access control matrix (master spec section 12.1).

Ingestion service uses a 4-role subset: super_admin, ucar_analyst,
institution_director, institution_admin.
"""

from enum import StrEnum

from backend.shared.exceptions import PermissionDenied


class Role(StrEnum):
    SUPER_ADMIN = "super_admin"
    UCAR_ANALYST = "ucar_analyst"
    INSTITUTION_DIRECTOR = "institution_director"
    INSTITUTION_ADMIN = "institution_admin"
    # Legacy platform roles kept for compatibility
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN_STAFF = "admin_staff"
    HR_MANAGER = "hr_manager"
    DEAN = "dean"
    PRESIDENT = "president"
    IT_ADMIN = "it_admin"
    MESRS_AUDITOR = "mesrs_auditor"


class Permission(StrEnum):
    VIEW_OWN_KPIS = "view_own_kpis"
    VIEW_INSTITUTION_KPIS = "view_institution_kpis"
    VIEW_ALL_INSTITUTIONS = "view_all_institutions"
    UPLOAD_DOCUMENTS = "upload_documents"
    APPROVE_EXTRACTIONS = "approve_extractions"
    CONFIGURE_THRESHOLDS = "configure_thresholds"
    MANAGE_USERS = "manage_users"
    TRIGGER_KPI_RECOMPUTE = "trigger_kpi_recompute"
    EXPORT_MESRS_REPORT = "export_mesrs_report"
    POST_PROJECTS = "post_projects"
    MANAGE_HIRING = "manage_hiring"
    GLOBAL_READ = "global_read"
    # Ingestion-specific
    IMPORT_HISTORICAL = "import_historical"
    OVERRIDE_QUARANTINE = "override_quarantine"
    UNLOCK_PERIOD = "unlock_period"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_DATA_REQUESTS = "manage_data_requests"
    PURGE_FILES = "purge_files"
    ROLLBACK_IMPORT = "rollback_import"


_ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),
    Role.UCAR_ANALYST: {
        Permission.VIEW_ALL_INSTITUTIONS,
        Permission.GLOBAL_READ,
        Permission.UPLOAD_DOCUMENTS,
        Permission.APPROVE_EXTRACTIONS,
        Permission.IMPORT_HISTORICAL,
        Permission.OVERRIDE_QUARANTINE,
        Permission.VIEW_AUDIT_LOG,
        Permission.MANAGE_DATA_REQUESTS,
        Permission.ROLLBACK_IMPORT,
        Permission.VIEW_INSTITUTION_KPIS,
        Permission.VIEW_OWN_KPIS,
        Permission.EXPORT_MESRS_REPORT,
    },
    Role.INSTITUTION_DIRECTOR: {
        Permission.VIEW_INSTITUTION_KPIS,
        Permission.VIEW_OWN_KPIS,
        Permission.UPLOAD_DOCUMENTS,
        Permission.APPROVE_EXTRACTIONS,
        Permission.EXPORT_MESRS_REPORT,
    },
    Role.INSTITUTION_ADMIN: {
        Permission.VIEW_INSTITUTION_KPIS,
        Permission.VIEW_OWN_KPIS,
        Permission.UPLOAD_DOCUMENTS,
    },
    Role.MESRS_AUDITOR: {
        Permission.VIEW_ALL_INSTITUTIONS,
        Permission.GLOBAL_READ,
        Permission.VIEW_AUDIT_LOG,
        Permission.EXPORT_MESRS_REPORT,
        Permission.VIEW_INSTITUTION_KPIS,
        Permission.VIEW_OWN_KPIS,
    },
    Role.IT_ADMIN: set(Permission),
    Role.DEAN: {
        Permission.VIEW_INSTITUTION_KPIS,
        Permission.VIEW_OWN_KPIS,
        Permission.UPLOAD_DOCUMENTS,
        Permission.APPROVE_EXTRACTIONS,
        Permission.CONFIGURE_THRESHOLDS,
        Permission.EXPORT_MESRS_REPORT,
        Permission.POST_PROJECTS,
    },
    Role.PRESIDENT: {
        Permission.VIEW_ALL_INSTITUTIONS,
        Permission.GLOBAL_READ,
        Permission.CONFIGURE_THRESHOLDS,
        Permission.EXPORT_MESRS_REPORT,
        Permission.POST_PROJECTS,
        Permission.VIEW_INSTITUTION_KPIS,
        Permission.VIEW_OWN_KPIS,
    },
}


def role_permissions(role: Role) -> set[Permission]:
    return _ROLE_PERMISSIONS.get(role, set())


def check_permission(role: Role, permission: Permission) -> bool:
    return permission in role_permissions(role)


def require(role: Role, permission: Permission) -> None:
    if not check_permission(role, permission):
        raise PermissionDenied(
            detail=f"Role '{role}' does not have permission '{permission}'"
        )
