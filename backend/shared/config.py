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
