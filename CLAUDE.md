# Health Data Platform (HDP)

## Architecture

Python-first multi-vertical health data platform. Three layers:

1. **Platform primitives** (`packages/hdp-*`) — canonical data models, audit,
   identity, consent, provenance, ingest, API, agent runtime, outbox.
2. **Verticals** (`verticals/<vertical>/<component>`) — domain-specific
   components. Currently: `home-health/hh-{oasis,scribe,hitl,emr-sync,mcp,skills}`.
3. **Apps** (`apps/*`) — composed deployables. Currently:
   `apps/home-health-scribe` wires a home-health deployment.

## Stack

Python >=3.13, uv workspace (16 members), FastAPI, SQLModel, Postgres 18,
MongoDB 7, Docker Compose for local dev.

## Project Structure

```
packages/           # Platform primitives (hdp-*)
verticals/
  home-health/      # hh-oasis, hh-scribe, hh-hitl, hh-emr-sync, hh-mcp, hh-skills
apps/
  home-health-scribe/   # Composed app
docker-compose.yml  # Postgres 18 + Mongo 7 + adminer
justfile            # Task runner (just --list)
pyproject.toml      # Workspace root + tool config
```

## Quality Tools

| Tool         | Purpose                    | Config              |
| ------------ | -------------------------- | ------------------- |
| ruff         | Lint + format              | `pyproject.toml`    |
| pytest       | Testing (importlib mode)   | `pyproject.toml`    |
| lefthook     | Git hooks                  | `lefthook.yml`      |
| commitlint   | Conventional commits       | `.commitlintrc.yaml`|
| coderabbit   | PR review                  | `.coderabbit.yaml`  |

Pytest uses `--import-mode=importlib` to avoid duplicate-basename collisions
across workspace members. Keep this — removing it breaks multi-package tests.

## Common Commands

| Command                  | Purpose                              |
| ------------------------ | ------------------------------------ |
| `just verify`            | Lint + tests (CI mirror)             |
| `just up` / `just down`  | Docker stack up/down                 |
| `just dev`               | Run home-health-scribe with reload   |
| `uv run pytest`          | Run all tests                        |
| `uv run ruff check`      | Lint                                 |
| `uv run ruff format`     | Format                               |
| `uvx lefthook install`   | Install git hooks (one-time)         |

## Conventions

- Conventional commits (`.commitlintrc.yaml` enforces scope-enum)
- Signed commits (do not use `--no-gpg-sign`)
- `vault/` gitignored (secrets/private artifacts)
