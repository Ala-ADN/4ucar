"""api-gateway — single FastAPI process that mounts every service router for local dev.

In production each service is its own pod behind nginx; locally we run one
process for fast iteration.
"""
