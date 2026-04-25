"""Alembic environment — pulls metadata from backend.models."""

from logging.config import fileConfig

from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def run_migrations_offline() -> None:
    raise NotImplementedError


def run_migrations_online() -> None:
    raise NotImplementedError


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
