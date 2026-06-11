"""AC-mapped test manifest (SK-0008 C7c anchor). One skip-bodied test per
acceptance criterion; bodies land during /agx:spec run phases."""

import pytest


# --- AC-001
def test_workspace_resolves_exactly_eight_members():
    pytest.skip("structural phase: uv sync exits 0; member dir count == 8")


# --- AC-002
def test_ci_mirror_green():
    pytest.skip("verify phase: just verify (ruff + pytest) exits 0")


# --- AC-003
def test_layering_invariant_holds():
    pytest.skip("verify phase: reference/check_layering.py exits 0")


# --- AC-004
def test_hdp_hitl_promoted_with_history():
    pytest.skip("structural phase: import hdp_hitl; git log --follow reaches hh-hitl commits")


# --- AC-005
def test_emr_sync_transport_seam_is_transport_agnostic():
    pytest.skip("structural phase: EmrSyncTransport imports; no httpx in protocol module")


# --- AC-006
def test_commitlint_scopes_match_member_set():
    pytest.skip("config phase: reference/check_commitlint.py exits 0")


# --- AC-007
def test_architecture_docs_reflect_eight_member_map():
    pytest.skip("docs phase: hdp-core present; removed member names absent; positioning intact")


# --- AC-008
def test_depth_markers_truthful():
    pytest.skip("verify phase: reference/check_depth_markers.py exits 0")


# --- AC-009
def test_concept_survival_all_submodules_import():
    pytest.skip("structural phase: all hdp_core.* / hdp_api.ingest / hh_scribe.* submodules import")


# --- AC-010
def test_pytest_collection_collision_free():
    pytest.skip("structural phase: uv run pytest -q --co exits 0 under importlib mode")


# --- AC-011
def test_dependency_union_zero_new_runtime_deps():
    pytest.skip("verify phase: reference/check_dep_union.py exits 0 against target-map.json")
