"""Environment-driven settings (pydantic-settings).

Each service imports `Settings` and reads from the process environment.
Concrete fields will be added per-service as scaffolding turns into implementation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def get_settings() -> Settings:
    raise NotImplementedError
