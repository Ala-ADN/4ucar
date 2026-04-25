"""Role-based access control matrix (see master spec section 12.1)."""

from enum import StrEnum


class Role(StrEnum):
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


def role_permissions(role: Role) -> set[Permission]:
    raise NotImplementedError


def require(permission: Permission):
    raise NotImplementedError
