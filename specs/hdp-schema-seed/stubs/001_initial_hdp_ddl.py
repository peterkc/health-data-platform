"""HDP initial DDL: extensions + canonical schema + HITL + OASIS.

STUB — copy to migrations/versions/001_initial_hdp_ddl.py during Phase 2.
Part of vault/specs/hdp-schema-seed/ (see design.md §Component Design).

Revision ID: 001_initial_hdp_ddl
Revises:
Create Date: 2026-04-23

Executes the statically-extracted HDP SQL files across three source trees in
filename-sorted order. The numeric prefix convention (00-, 01-, 10-, 20-, 30-,
40-, 50-, 60-, 99-) carries dependency order across trees:

  packages/hdp-canonical/sql/
    00-extensions.sql
    01-functions.sql
    10-reference.sql
    20-identity.sql
    30-silver.sql
    40-operational.sql
    99-triggers.sql
  packages/hdp-hitl/sql/
    50-hitl.sql
  verticals/home-health/hh-oasis/sql/
    60-oasis.sql

Canonical content originates from vault/research/table-designs.md (migrated
from mvp-schema). HITL + OASIS content is authored fresh in this spec.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from alembic import op

# Alembic revision identifiers.
revision: str = "001_initial_hdp_ddl"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REPO_ROOT = Path(__file__).parent.parent.parent.parent
# Safety: packages/hdp-canonical/tests/test_sql_discovery.py asserts each of these
# directories exists, is non-empty, and contains files matching NN-name.sql so a
# silent path rename cannot reduce this migration to a no-op.
SQL_DIRS = [
    REPO_ROOT / "packages" / "hdp-canonical" / "sql",
    REPO_ROOT / "packages" / "hdp-hitl" / "sql",
    REPO_ROOT / "verticals" / "home-health" / "hh-oasis" / "sql",
]


def upgrade() -> None:
    """Collect sql/*.sql across three source trees, sort by basename, op.execute() each."""
    all_sql_files: list[Path] = []
    for sql_dir in SQL_DIRS:
        if sql_dir.exists():
            all_sql_files.extend(sql_dir.glob("*.sql"))
    for sql_file in sorted(all_sql_files, key=lambda p: p.name):
        op.execute(sql_file.read_text())


def downgrade() -> None:
    """Initial migration is not reversible in scaffold phase.

    Clean-slate reset is via `just db-reset` (drops the postgres-data volume),
    not via Alembic. A reversible downgrade would require explicit DROP
    statements per table in reverse dependency order, which we defer to
    post-scaffold hardening.
    """
    raise NotImplementedError(
        "HDP initial DDL is not reversible via Alembic in scaffold phase; "
        "use `just db-reset` (drop postgres-data volume) to start clean."
    )
