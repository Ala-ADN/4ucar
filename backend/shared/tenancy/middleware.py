"""ASGI middleware: extract tenant from JWT claims, bind to contextvar, set Postgres GUC."""


class TenantMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        raise NotImplementedError
