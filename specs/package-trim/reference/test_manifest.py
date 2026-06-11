"""AC-mapped test manifest (SK-0008 C7c anchor). One skip-bodied test per
acceptance criterion; bodies land during /agx:spec run phases.

Run contract: invoke with the workspace root as cwd (works against the main
checkout or a feature worktree): `cd <repo-root> && uv run pytest <this file>`.
Structural-phase bodies landed at structural-phase close; later-phase ACs stay
skip-bodied until their phase runs."""

import re
import subprocess
from pathlib import Path

ROOT = Path.cwd()


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


# --- AC-001
def test_workspace_resolves_exactly_eight_members():
    sync = _run(["uv", "sync", "--all-packages"])
    assert sync.returncode == 0, sync.stderr[-1000:]
    members = [
        p for base in ("packages", "verticals/home-health", "apps")
        for p in (ROOT / base).iterdir() if p.is_dir()
    ]
    assert len(members) == 8, sorted(str(p) for p in members)


# --- AC-002
def test_ci_mirror_green():
    res = _run(["just", "verify"])
    assert res.returncode == 0, (res.stdout + res.stderr)[-1000:]


# --- AC-003
def test_layering_invariant_holds():
    res = _run(["python3", str(Path(__file__).with_name("check_layering.py"))])
    assert res.returncode == 0, res.stderr[-1000:]


# --- AC-004
def test_history_preserved_per_merge_target():
    samples = [
        "packages/hdp-hitl/src/hdp_hitl/__init__.py",
        "packages/hdp-core/src/hdp_core/audit/__init__.py",
        "packages/hdp-api/src/hdp_api/ingest/__init__.py",
        "verticals/home-health/hh-scribe/src/hh_scribe/oasis/__init__.py",
    ]
    for f in samples:
        res = _run(["git", "log", "--follow", "--oneline", "--", f])
        commits = [line for line in res.stdout.splitlines() if line.strip()]
        assert len(commits) >= 2, f"{f}: --follow reaches only {len(commits)} commit(s)"


# --- AC-005
def test_emr_sync_transport_seam_is_transport_agnostic():
    imp = _run(["uv", "run", "python", "-c", "from hh_emr_sync.transport import EmrSyncTransport"])
    assert imp.returncode == 0, imp.stderr[-1000:]
    module = ROOT / "verticals/home-health/hh-emr-sync/src/hh_emr_sync/transport.py"
    httpx_imports = [
        line for line in module.read_text().splitlines()
        if re.match(r"^\s*(import|from)\s+httpx", line)
    ]
    assert not httpx_imports, httpx_imports


# --- AC-006
def test_commitlint_scopes_match_member_set():
    res = _run(["python3", str(Path(__file__).with_name("check_commitlint.py"))])
    assert res.returncode == 0, res.stderr[-1000:]


# --- AC-007
def test_architecture_docs_reflect_eight_member_map():
    readme = (ROOT / "README.md").read_text()
    claude = (ROOT / "CLAUDE.md").read_text()
    assert "hdp-core" in readme and "hdp-core" in claude
    for retired in ("hdp-canonical", "hdp-provenance", "hh-oasis"):
        assert retired not in readme and retired not in claude, retired
    assert "AI-native workflow and governance layer" in readme


# --- AC-008
def test_depth_markers_truthful():
    res = _run(["python3", str(Path(__file__).with_name("check_depth_markers.py"))])
    assert res.returncode == 0, res.stderr[-1000:]


# --- AC-009
def test_concept_survival_all_submodules_import():
    imp = _run([
        "uv", "run", "python", "-c",
        "import hdp_core.canonical, hdp_core.audit, hdp_core.identity, "
        "hdp_core.consent, hdp_core.provenance, hdp_core.outbox, "
        "hdp_api.ingest, hh_scribe.oasis, hh_scribe.skills, hh_scribe.mcp",
    ])
    assert imp.returncode == 0, imp.stderr[-1000:]


# --- AC-010
def test_pytest_collection_collision_free():
    collect = _run(["uv", "run", "pytest", "-q", "--co", "packages", "verticals", "apps"])
    assert collect.returncode == 0, (collect.stdout + collect.stderr)[-1000:]


# --- AC-011
def test_dependency_union_zero_new_runtime_deps():
    res = _run(["python3", str(Path(__file__).with_name("check_dep_union.py"))])
    assert res.returncode == 0, res.stderr[-1000:]
