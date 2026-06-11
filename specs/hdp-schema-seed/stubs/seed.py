"""STUB — copy to scripts/seed.py and refine during Phase 3 (verify-seed).

Part of vault/specs/hdp-schema-seed/ (see design.md §Component Design).

Seed HDP reference tables and one test patient. Idempotent via
ON CONFLICT DO NOTHING on every INSERT. Each _seed_* helper returns
cur.rowcount so the orchestrator can report inserted counts per table.
"""
from __future__ import annotations

import os

import psycopg
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.get_logger("hdp.seed")


def seed_all(conn_str: str) -> dict[str, int]:
    """Run every seed helper inside a single transaction.

    Bootstrap writes produce audit_changes rows with batch_id = NULL because
    no hdp.audit_batch_id session variable is set (see design.md Decision 8).
    """
    log.info("seed.start")
    counts: dict[str, int] = {}
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            counts["ref_hom_nodes"] = _seed_hom_nodes(cur)
            counts["ref_source_adapters"] = _seed_source_adapters(cur)
            counts["ref_organizations"] = _seed_organizations(cur)
            counts["ref_analyte_conversions"] = _seed_analyte_conversions(cur)
            counts["ref_record_type_schemas"] = _seed_record_type_schemas(cur)
            counts["ref_drug_classes"] = _seed_drug_classes(cur)
            counts["loinc_crosswalk"] = _seed_loinc_crosswalk(cur)
            counts["policy_rules"] = _seed_policy_rules(cur)
            counts["test_patient"] = _seed_test_patient(cur)
        conn.commit()
    log.info("seed.done", counts=counts)
    return counts


# Each _seed_* helper issues INSERTs with ON CONFLICT DO NOTHING and returns cur.rowcount.
# Bodies are filled in during Phase 3 execution against the canonical table shapes in sql/.


def _seed_hom_nodes(cur: psycopg.Cursor) -> int:
    """Body-systems hierarchy, top-down. >= 10 rows (cardiovascular, metabolic, ...)."""
    raise NotImplementedError


def _seed_source_adapters(cur: psycopg.Cursor) -> int:
    """>= 4 rows: fhir, csv, oura, biomarkers minimum."""
    raise NotImplementedError


def _seed_organizations(cur: psycopg.Cursor) -> int:
    """>= 1 stub organization row for FK anchoring."""
    raise NotImplementedError


def _seed_analyte_conversions(cur: psycopg.Cursor) -> int:
    """Minimal unit conversions (UCUM-ready)."""
    raise NotImplementedError


def _seed_record_type_schemas(cur: psycopg.Cursor) -> int:
    """Record-type schema stub rows."""
    raise NotImplementedError


def _seed_drug_classes(cur: psycopg.Cursor) -> int:
    """Drug-class stub rows."""
    raise NotImplementedError


def _seed_loinc_crosswalk(cur: psycopg.Cursor) -> int:
    """>= 5 LOINC crosswalk rows for the reviewer gold path."""
    raise NotImplementedError


def _seed_policy_rules(cur: psycopg.Cursor) -> int:
    """>= 1 policy rule. Trigger on policy_rules fires; produces NULL-batched audit row."""
    raise NotImplementedError


def _seed_test_patient(cur: psycopg.Cursor) -> int:
    """One row each in persons + patients + person_identifiers, FK-consistent."""
    raise NotImplementedError


if __name__ == "__main__":
    result = seed_all(os.environ["DATABASE_URL"])
    for name, rows in result.items():
        print(f"  {name}: +{rows} rows")
