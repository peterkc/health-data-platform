"""STUB — copy to migrations/env.py and refine during Phase 2 (mvs-ddl).

Part of vault/specs/hdp-schema-seed/ (see design.md §Component Design).

Alembic env.py: offline + online migration runners. At this spec there are no
SQLAlchemy models, so target_metadata is None. When the Repository layer
introduces models, replace target_metadata with the models' Base.metadata to
enable `alembic revision --autogenerate`.
"""
from __future__ import annotations

import os
from logging.config import fileConfig

import structlog
from alembic import context
from sqlalchemy import engine_from_config, pool

# Structlog wiring so migration runs emit structured logs consistent with the
# rest of the HDP stack (hdp-observability). Local dev prints to stderr;
# production/CI can attach an OTLP exporter without touching this file.
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.get_logger("hdp.migrations")

config = context.config

# Override sqlalchemy.url from env var if present.
if db_url := os.environ.get("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# At this spec: no SQLAlchemy models yet. The Repository-layer spec will set this
# to `Base.metadata` from the models module, enabling `alembic revision --autogenerate`.
#
# WARNING: with target_metadata=None, `alembic revision --autogenerate` produces
# an EMPTY migration silently — no error, no warning. Before running autogenerate
# when models arrive, ensure target_metadata points to the SQLAlchemy Base.metadata
# and that models match the existing DB schema (first autogen should be a no-op revision).
target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    log.info("alembic.offline.start", url=url)
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
    log.info("alembic.offline.done")


def run_migrations_online() -> None:
    log.info("alembic.online.start")
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    log.info("alembic.online.done")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
