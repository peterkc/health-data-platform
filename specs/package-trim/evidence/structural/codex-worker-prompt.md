---
version: stub-v0
role: worker
mode: implement
phase: structural
spec: package-trim
---

You are executing phase structural of spec "package-trim".

## Goal

17 uv workspace members become 8 via history-preserving `git mv`; each merged
member's smoke test is relocated-and-renamed into the survivor's tests/ tree
(NFR-004); the workspace syncs, imports prove concept survival, test collection
is collision-free, and the transport module is httpx-free.

Shared fate: the uv workspace cannot sync with dangling member references —
removing hdp-canonical while hh-oasis still depends on it breaks every
downstream command. Partial maps are not keepable intermediates; the member-map
rewrite lands together or not at all. The `EmrSyncTransport` Protocol stub rides
along because hh-emr-sync's pyproject is rewritten here exactly once.

## Context

Working directory (the repo worktree): `/Volumes/health-data/.claude/worktrees/package-trim`
All repo paths below are relative to it.

Read these spec sources FIRST (absolute paths, read-only — they live outside
the worktree):

- `/Volumes/health-data/vault/specs/package-trim/tasks.yaml` — `manifest:` is
  the single source of truth: every file/dir touched, with status + purpose.
  Execute the manifest entries for the structural phase only (see Out of scope).
- `/Volumes/health-data/vault/specs/package-trim/requirements.md` — FR-001..006,
  FR-009, NFR-001..004 bind this phase.
- `/Volumes/health-data/vault/specs/package-trim/design.md` — § Architecture +
  § Decisions (submodule layout, async-push rationale).
- `/Volumes/health-data/vault/specs/package-trim/reference/target-map.json` —
  per-member dependency unions post-trim (SoT for every pyproject rewrite).
- `/Volumes/health-data/vault/specs/package-trim/reference/emr_sync_transport.py`
  — the `EmrSyncTransport` Protocol stub. Land it verbatim as
  `verticals/home-health/hh-emr-sync/src/hh_emr_sync/transport.py`.

Target map (17 → 8 members):

| Survivor | Absorbs (as submodules) |
| --- | --- |
| `packages/hdp-core` (NEW) | hdp-canonical, hdp-audit, hdp-identity, hdp-consent, hdp-provenance, hdp-outbox → `hdp_core.{canonical,audit,identity,consent,provenance,outbox}` |
| `packages/hdp-api` | hdp-ingest → `hdp_api.ingest` |
| `packages/hdp-agent` | — (unchanged) |
| `packages/hdp-observability` | — (unchanged; do NOT touch its README this phase) |
| `packages/hdp-hitl` (NEW location) | whole-package `git mv` of `verticals/home-health/hh-hitl/` (src + tests together; import name `hdp_hitl`) |
| `verticals/home-health/hh-scribe` | hh-oasis, hh-skills, hh-mcp → `hh_scribe.{oasis,skills,mcp}` |
| `verticals/home-health/hh-emr-sync` | — standalone; deps remap hdp-outbox → hdp-core; gains `transport.py` stub |
| `apps/home-health-scribe` | deps remap: hh-oasis removed (now inside hh-scribe), hh-hitl → hdp-hitl |

Mechanics that are binding, not advisory:

1. **Every move uses `git mv`** (NFR-001) — src trees, test files, and the
   whole-package hh-hitl move. No copy-then-delete.
2. **Submodule layout** (FR-002/004/005): e.g.
   `git mv packages/hdp-audit/src/hdp_audit packages/hdp-core/src/hdp_core/audit`
   (rename the inner package dir to the submodule name as part of the move).
   `packages/hdp-core/src/hdp_core/__init__.py` is a new file. Same pattern for
   `hdp_api/ingest` and `hh_scribe/{oasis,skills,mcp}`.
3. **Test relocate-and-rename** (NFR-004): each merged member's
   `tests/test_smoke.py` → survivor's `tests/test_<submodule>_smoke.py` via
   `git mv` (e.g. `packages/hdp-audit/tests/test_smoke.py` →
   `packages/hdp-core/tests/test_audit_smoke.py`). New `tests/__init__.py` in
   hdp-core's tests/ if the design manifest says so. hdp-hitl is a whole-package
   move — its test basename survives unchanged. Fix any intra-test imports so the
   renamed tests still pass.
4. **hh-hitl import rename**: after the move the distribution is `hdp-hitl` and
   the import package is `hdp_hitl` — `git mv` the inner
   `src/hh_hitl` dir to `src/hdp_hitl` and update its pyproject name/deps
   (deps remap to hdp-core per target-map.json).
5. **Transport stub** (FR-006): land the reference stub verbatim as
   `hh_emr_sync/transport.py`. `push` is `async def`; `health` stays sync; the
   module must contain NO `import httpx` / `from httpx` statement.
6. **pyproject rewrites**: root `pyproject.toml` `tool.uv.sources` +
   `tool.uv.workspace members` shrink to exactly the 8 survivors; each surviving
   member's `[project] dependencies` must exactly equal the union in
   `target-map.json` (NFR-002 — zero new runtime deps; dedup). Remove merged
   members' pyprojects with their directories (`git rm` happens implicitly via
   `git mv` of contents + removing the leftover shell — ensure nothing of the
   merged member dirs remains).
7. **uv.lock**: regenerate via `uv lock` after the member-map rewrite, then
   `uv sync`.
8. **Member READMEs** (FR-009): new/merged survivors (`hdp-core`, `hdp-api`,
   `hdp-hitl`, `hh-scribe`, `hh-emr-sync`) carry a README with a truthful
   canonical Depth marker line `**Depth**: SKEL` (they are interface-only
   shells). Preserve useful prose from absorbed members' READMEs as concept
   bullets if trivial; do not invent content. Do NOT touch
   `packages/hdp-observability/README.md`, root `README.md`, or `CLAUDE.md`.
9. **Layering** (NFR-003): no `packages/*` member may depend on a vertical or
   app; no vertical on an app.

Out of scope for this phase (later phases own them — do not touch):

- `.commitlintrc.yaml` (config phase)
- root `README.md`, `CLAUDE.md`, `packages/hdp-observability/README.md` (docs phase)
- Any `git commit` — leave ALL changes uncommitted/staged in the working tree.
  `git mv` staging is expected and fine; do not create commits.

## Grounding

Resolve every concrete verifiable value — commit SHA, hash, version
string, numeric ID, file path, symbol / API name — via a tool command
(`git ls-remote`, `gh api`, `grep`, `cargo metadata`) and quote it from
the output. Never emit such a value from memory or pattern-matching, even
when not asked to "verify."

If a required command fails (non-zero exit), report it with the exit code
and reason. Do not improvise, reconstruct, or substitute a value to appear
complete. Trace every claim to tool output.

## Validation

After implementing, run (from the worktree root):

```bash
uv sync && uv run python -c 'import hdp_core.canonical, hdp_core.audit, hdp_core.identity, hdp_core.consent, hdp_core.provenance, hdp_core.outbox, hdp_api.ingest, hdp_hitl, hh_scribe.oasis, hh_scribe.skills, hh_scribe.mcp, hh_emr_sync.transport' && ! grep -Eq '^[[:space:]]*(import|from)[[:space:]]+httpx' verticals/home-health/hh-emr-sync/src/hh_emr_sync/transport.py && uv run pytest -q --co >/dev/null && test "$(ls -d packages/*/ verticals/home-health/*/ apps/*/ | wc -l | tr -d ' ')" = '8'
```

Report the exit code and the tail of output (failure context) in your final response.

## Output

Summarize:

- Files changed (path + 1-line purpose each)
- Tests run (command + result)
- Any deviations from the phase goal + rationale
