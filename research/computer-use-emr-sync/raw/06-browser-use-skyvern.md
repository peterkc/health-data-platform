# Source 06 — browser-use and Skyvern

Gathered 2026-06-11 via agent fan-out against github.com/browser-use/browser-use,
github.com/browser-use/workflow-use, github.com/Skyvern-AI/skyvern,
docs.browser-use.com, skyvern.com/docs.

## browser-use (MIT, v0.13.1 2026-06-10, 98.3k stars, Python >=3.11)

- Not strictly agent-first: a documented direct-control "Actor" layer
  (`BrowserSession`, page/element-level `click/fill/goto/evaluate`, CDP attach)
  works with zero LLM calls — though its docs URL path says `legacy/`
  (placement in transition, UNVERIFIED post-0.13).
- **Not Playwright**: 0.6.0 removed Playwright wholesale for an in-house CDP
  client (`cdp-use`) + event bus (release "bye-playwright").
- DOM serialization pipeline (injected `buildDomTree.js` → visible/interactive
  filter → indexed `selector_map` → compact LLM rendering) is modular and
  reachable standalone via `get_state()` — the best off-the-shelf MIT
  page-representation for a drift-recovery fallback. Known gaps: iframes only
  when scrolled into view (#3619), JS-listener-only clickables missed (#832).
- workflow-use sister project = record-once / replay-deterministic /
  agent-self-heal — exactly the right shape, but "very early development, not
  for production" per its README, release-stale (v0.2.11, 2025-11), and
  **AGPL-3.0** unlike the MIT core.
- Pre-1.0 instability is structural: foundation swaps twice in 18 months
  (Playwright→cdp-use; 0.13 Rust-core beta). Pin-and-vendor mandatory.
  PostHog telemetry baked in (opt-out).

## Skyvern (AGPL-3.0, Python >=3.11 <3.14)

- "Vision-first" marketing, hybrid reality: builds an interactable element
  tree across frames, injects stable `skyvern-id` attributes, resolves actions
  to CSS selectors (not pixels); LLM sees annotated screenshot + token-capped
  serialized tree, answers in element IDs (`webeye/scraper/scraper.py`).
  `IncrementalScrapePage` mutation-observer delta-scraping is a smart
  drift-detection primitive.
- Form-filling on unseen portals = LLM schema-mapping over that tree;
  vendor-reported WebBench 64.4% (best on WRITE), WebVoyager 85.8%
  (UNVERIFIED independently). Every run consults the LLM — no deterministic
  replay of a learned mapping.
- Self-host: docker-compose with Postgres — mirrors the HDP stack. Workflow
  engine has borrowable failure semantics: per-block `continue_on_failure`,
  loop-scoped `next_loop_on_failure`, error-code mapping, dual
  Complete-if/Terminate-if AI validation, Human Interaction pause block
  (HITL-shaped). No durable checkpoint/resume documented.
- AGPL read (license-text interpretation, not legal advice): internal
  self-hosted use is operationally fine (network clause triggers on *modified*
  versions, beneficiaries are the org's own users; internal use is not
  conveying). A hard `import skyvern` in an MIT-licensed driver repo would
  make the distributed whole AGPL-governed — HTTP-API integration or
  reference-architecture borrowing only.
