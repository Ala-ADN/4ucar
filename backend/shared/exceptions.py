"""Bilingual error envelope and shared exception hierarchy.

Mirrors the standard error format defined in section 11 of the master spec:
    { error: { code, message_fr, message_ar, detail, tenant_id, ... } }
"""


class UcarError(Exception):
    """Base class for all domain-level errors raised by services."""


class ValidationFailed(UcarError):
    pass


class PermissionDenied(UcarError):
    pass


class NotFound(UcarError):
    pass


class TenantScopeViolation(UcarError):
    pass


class IntegrationFailed(UcarError):
    pass
