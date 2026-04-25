"""MinIO/S3 client: per-tenant bucket, pre-signed URLs (15 min TTL)."""


def get_minio_client():
    raise NotImplementedError


def tenant_bucket(institution_code: str) -> str:
    raise NotImplementedError


def presigned_url(bucket: str, key: str, expires_seconds: int = 900) -> str:
    raise NotImplementedError
