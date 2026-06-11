# Test matrix — behavior x backend

Backends: **unit** (no browser; fakes/local fs), **sandbox** (live local
OpenEMR via docker-compose, synthetic data), **static** (build/CI gates and
artifact greps). Every AC has a home; static rows are gates, not pytest.

| Behavior | AC | Backend |
| --- | --- | --- |
| Repo public + MIT + CI green | AC-001 | static |
| Sandbox up, pinned, seeded | AC-002 | sandbox |
| Field round-trip E2E (login→read→write→verify) | AC-003 | sandbox |
| SIGKILL mid-job → resume, no duplicate write | AC-004 | sandbox |
| Audit replay complete + ordered | AC-005 | sandbox |
| Thin API job lifecycle + OpenAPI | AC-006 | sandbox |
| Failure classification (drift, dead-session) | AC-007 | sandbox |
| Egress allowlist blocks + logs | AC-008 | unit |
| storage_state custody (location, mode, absence) | AC-009 | unit |
| Hub taxonomy >=3 rows w/ hardening recs | AC-010 | static |
| Fallback seam + zero-LLM invariant | AC-011 | sandbox |
| Negative-space trust boundaries | AC-012 | unit |
| Public-reader hygiene grep (repo + hub diff) | AC-013 | static |
| Golden audit event validates against models | — | static (create gate C2) |
| Lint + type check (ruff, mypy) | — | static (CI, NFR-001) |
