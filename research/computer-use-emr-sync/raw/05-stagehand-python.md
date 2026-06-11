# Source 05 — Stagehand Python SDK (Browserbase)

Gathered 2026-06-11 via agent fan-out against github.com/browserbase/stagehand-python,
github.com/browserbase/stagehand, docs.stagehand.dev, pypi.org/project/stagehand.

## Architecture

- v3 Python SDK is a Stainless-generated HTTP client; every primitive is a
  REST/SSE call to a Stagehand server (Node/Fastify wrapping the TS core).
- Three server topologies: Browserbase cloud (default), **local embedded**
  (`Stagehand(server="local")` spawns a Node SEA binary shipped inside
  platform-specific wheels — no Browserbase account, no Node install), or
  self-hosted standalone (`STAGEHAND_API_URL`).
- Server is open source (MIT, `packages/server-v3` in the stagehand monorepo).
- Chain: Python client → REST/SSE → server-v3 → CDP → Chromium (local launch,
  cloud session, or BYOB `cdpUrl`).
- Docs lag code: the migration guide omits the embedded-server local mode that
  the SDK source ships (`src/stagehand/_custom/sea_binary.py`).

## Fit signals

- **BYOB pattern maps exactly onto DOM-first/LLM-fallback**: launch your own
  Playwright browser, pass its CDP URL + the Playwright `page` object into
  `observe/act/extract` — deterministic loop stays native Playwright,
  framework touches only the fallback. `observe()` returns structured Actions
  replayable through `act()` without fresh inference.
- Sync + async clients, Pydantic models, SSE streaming of long-running ops.
- MIT end-to-end; SDK v3.21.0 (2026-05-29), weekly cadence; monorepo 23.1k
  stars; Python repo 487 stars (young).

## Gaps / risks

- **Python lags TS on the fallback-quality features**: no act-level caching
  (`cacheDir`/server cache are TS-only); v2 `self_heal` flag removed; custom
  LLM clients and logging config unsupported. Only agent-level `should_cache`
  exists, returning a serialized cache entry with **no verified replay-submission
  path** — the cache/replay store is build-it-yourself (UNVERIFIED whether the
  server replays entries via another route).
- Mandatory extra moving part even locally (Node SEA subprocess: supervision,
  ports, version skew, platform-specific wheels).
- Cloud gravity: captcha, stealth, session recordings, server cache, search
  are Browserbase-cloud-only.
