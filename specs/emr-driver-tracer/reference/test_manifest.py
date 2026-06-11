"""AC-mapped test manifest for emr-driver-tracer (one skip-bodied test per AC).

Each test names the phase suite where the real assertion lands; tags are the
spec_coverage.py C7c anchors. Backends per reference/test_matrix.md:
unit (no browser), sandbox (live local OpenEMR), static (build/CI gates).
"""

import pytest


# --- AC-001
def test_repo_public_mit_ci_green() -> None:
    """gh repo view reports PUBLIC+MIT; fresh clone pytest green; CI green. [static]"""
    pytest.skip("bootstrap phase: verified by gh repo view + CI run")


# --- AC-002
def test_sandbox_up_pinned_seeded() -> None:
    """compose up serves OpenEMR login; version pinned; synthetic patient retrievable. [sandbox]"""
    pytest.skip("bootstrap phase: tests/test_sandbox.py")


# --- AC-003
def test_field_roundtrip_e2e() -> None:
    """run field-roundtrip exits 0; final audit event = read-after-write verified. [sandbox]"""
    pytest.skip("tracer phase: tests/test_roundtrip.py")


# --- AC-004
def test_sigkill_resume_no_duplicate_write() -> None:
    """SIGKILL mid-job; resume completes; field applied exactly once. [sandbox]"""
    pytest.skip("failure-injection phase: tests/test_resume.py")


# --- AC-005
def test_audit_replay_complete_and_ordered() -> None:
    """audit replay prints every action in seq order; count matches recorded actions. [sandbox]"""
    pytest.skip("tracer phase: tests/test_audit.py")


# --- AC-006
def test_thin_api_job_lifecycle() -> None:
    """POST /jobs, GET /jobs/{id}, POST /jobs/{id}/resume work; /openapi.json served. [sandbox]"""
    pytest.skip("tracer phase: tests/test_api.py")


# --- AC-007
def test_failure_classification() -> None:
    """Induced selector miss -> selector-drift; induced logout -> dead-session. [sandbox]"""
    pytest.skip("failure-injection phase: tests/test_classification.py")


# --- AC-008
def test_egress_allowlist_blocks_and_logs() -> None:
    """Request to non-allowlisted host blocked; blocked AuditEvent logged. [unit]"""
    pytest.skip("tracer phase: tests/test_egress.py")


# --- AC-009
def test_storage_state_custody() -> None:
    """storage_state outside repo tree, mode 0600, absent from audit/checkpoint payloads. [unit]"""
    pytest.skip("tracer phase: tests/test_custody.py")


# --- AC-010
def test_hub_taxonomy_rows() -> None:
    """Hub taxonomy table gains >=3 observed rows each with a hardening rec. [static]"""
    pytest.skip("hub-feedback phase: grep gate on vault/research/computer-use-emr-sync/README.md")


# --- AC-011
def test_fallback_seam_and_zero_llm_invariant() -> None:
    """Fallback off: zero LLM calls in audit. Fallback on: induced drift recovers or halts cleanly. [sandbox]"""
    pytest.skip("fallback-eval phase: tests/test_fallback.py")


# --- AC-012
def test_negative_space_trust_boundaries() -> None:
    """Malformed CLI args / env / API bodies / selector maps -> typed error, no crash, no EMR write. [unit]"""
    pytest.skip("tracer phase: tests/test_negative.py")


# --- AC-013
def test_public_reader_hygiene_grep() -> None:
    """Hygiene grep over repo content + hub diff returns zero application-context hits. [static]"""
    pytest.skip("merge phase: grep gate; term list in bead hdp-8qn (never in public artifacts)")
