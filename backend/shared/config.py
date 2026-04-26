"""Environment-driven settings (pydantic-settings).

Each service imports `Settings` and reads from the process environment.
Add fields as services come online; keep `extra="ignore"` so unrecognised
env vars from neighbouring services don't trip startup.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    # Default points at a local docker-compose Postgres for dev. Override
    # via DATABASE_URL env var. Use the asyncpg driver: postgresql+asyncpg://...
    database_url: str = (
        "postgresql+asyncpg://ucar:change-me@localhost:5432/ucar"
    )
    database_echo: bool = False  # set true to log SQL


@lru_cache
def get_settings() -> Settings:
    return Settings()
    # Application
    app_env: str = "local"
    app_log_level: str = "INFO"
    app_secret_key: str = "change-me"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ucar"
    postgres_user: str = "ucar"
    postgres_password: str = "change-me"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Elasticsearch
    es_url: str = "http://localhost:9200"

    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "ucar"
    keycloak_client_id: str = "ucar-backend"
    keycloak_client_secret: str = "change-me"

    # Observability
    sentry_dsn: str = ""
    prometheus_enabled: bool = True

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_dsn_sync(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
