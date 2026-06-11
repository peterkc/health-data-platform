"""STUB — merge into apps/home-health-scribe/src/home_health_scribe/main.py
during Phase 1 (tracer-scaffold).

Part of vault/specs/hdp-schema-seed/ (see design.md §Component Design).

/health serves as both a liveness check and a phase indicator:
  - Pre-DDL:           reports zero tables, null alembic_version, null hom_nodes_seeded
  - Post-DDL pre-seed: reports N tables, alembic_version = "001_initial_hdp_ddl", hom_nodes_seeded = 0
  - Post-seed:         reports N tables + alembic_version + hom_nodes_seeded >= 10

State-dependent fields wrap their queries in try/except for UndefinedTable
and roll back the cursor to preserve connection usability across queries.
"""
from __future__ import annotations

import os

import psycopg
from fastapi import HTTPException


async def health() -> dict[str, object]:
    try:
        with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
            with conn.cursor() as cur:
                # Core: Postgres version + uuidv7 availability (always queryable).
                cur.execute("SELECT version(), (uuidv7() IS NOT NULL)")
                row = cur.fetchone()
                if row is None:
                    raise HTTPException(status_code=500, detail="empty response")
                version, has_uuidv7 = row

                # Schema state: public base table count.
                cur.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
                )
                (tables_count,) = cur.fetchone() or (0,)

                # Migration state: current Alembic revision (null pre-DDL).
                alembic_version: str | None = None
                try:
                    cur.execute("SELECT version_num FROM alembic_version LIMIT 1")
                    av_row = cur.fetchone()
                    alembic_version = av_row[0] if av_row else None
                except psycopg.errors.UndefinedTable:
                    conn.rollback()

                # Seed state: ref_hom_nodes row count (null pre-DDL, 0 pre-seed, >=10 post-seed).
                hom_nodes_seeded: int | None = None
                try:
                    cur.execute("SELECT COUNT(*) FROM ref_hom_nodes")
                    (hom_nodes_seeded,) = cur.fetchone() or (0,)
                except psycopg.errors.UndefinedTable:
                    conn.rollback()
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail=f"db unreachable: {exc}") from exc

    return {
        "status": "ok",
        "postgres": version.split()[1],
        "uuidv7": bool(has_uuidv7),
        "tables_count": tables_count,
        "alembic_version": alembic_version,
        "hom_nodes_seeded": hom_nodes_seeded,
    }
