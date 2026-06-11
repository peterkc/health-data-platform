# health-data-platform task runner
# Run `just --list` for the full recipe catalog.

set shell := ["bash", "-euo", "pipefail", "-c"]

default: verify

# --- Docker Compose -----------------------------------------------------------

# Bring up Postgres 18 + Mongo 7 + adminer in the background.
# Bootstraps .env from .env.example on first run — compose has no inline
# password defaults, so .env must exist.
up:
    @[ -f .env ] || cp .env.example .env
    docker compose up -d

# Tear down the stack, leaving volumes in place.
down:
    docker compose down

# Follow combined service logs.
logs:
    docker compose logs -f

# Bring up the observability stack (otel collector → stdout) alongside the
# base services. Additive; safe to run when the base stack is already up.
observability-up:
    docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Tear down observability collector (leaves base services running).
observability-down:
    docker compose -f docker-compose.yml -f docker-compose.observability.yml down

# --- Database ----------------------------------------------------------------

# Apply DB migrations. Real implementation lands once hdp-canonical / hdp-audit
# schemas exist; this stub keeps the command surface stable.
db-migrate:
    @echo "db-migrate: stub — migrations will be wired up once schemas land."

# Seed reference data + a sample visit. Stub until fixtures exist.
seed:
    @echo "seed: stub — seed data arrives with the hh-scribe implementation."

# --- Test / lint -------------------------------------------------------------

# Unit-test the entire workspace.
test:
    uv run pytest

# Integration suite (separate marker/path once it exists).
test-integration:
    uv run pytest -m integration || echo "no integration tests yet"

# Local dev server for the composed app.
dev:
    uv run uvicorn home_health_scribe.main:app --reload --host 0.0.0.0 --port 8000

# Lint + format check, no modifications — the CI lint gate.
lint:
    uv run ruff check .
    uv run ruff format --check .

# Auto-format in place.
fmt:
    uv run ruff format .

# Static type-check shipped source (src dirs only; tests excluded).
typecheck:
    uv run mypy packages/*/src verticals/home-health/*/src apps/*/src

# Tests with coverage (term-missing locally, xml + junit for CI upload).
cov:
    uv run pytest --cov --cov-report=term-missing --cov-report=xml --junitxml=junit.xml

# Audit resolved dependencies for known CVEs (skips first-party packages).
audit:
    uv run --with pip-audit pip-audit --skip-editable

# Full verification gate: lint + type-check + tests.
verify: lint typecheck test

# Mirror GitHub Actions locally (lint + type-check + tests + dependency audit).
ci: lint typecheck test audit

# Install git hooks (run once after cloning).
install-hooks:
    uvx lefthook install

# Remove caches and build artifacts (leaves .venv alone).
clean:
    find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache -o -name "*.egg-info" -o -name dist -o -name build \) -prune -exec rm -rf {} +
