"""FastAPI dependency factories: current user, current tenant, permission checks."""


def get_current_user():
    raise NotImplementedError


def get_current_tenant():
    raise NotImplementedError
