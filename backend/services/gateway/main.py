"""Gateway FastAPI app — mounts all service routers under /v1/."""

from fastapi import FastAPI

app = FastAPI(title="ucar-api-gateway")
