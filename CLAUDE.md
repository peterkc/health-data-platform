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


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
