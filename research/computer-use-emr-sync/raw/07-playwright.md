# Source 07 — Playwright (Python)

Gathered 2026-06-11 via agent fan-out against playwright.dev/python,
github.com/microsoft/playwright-python, pypi.org/project/playwright.

Apache-2.0, Microsoft-governed, ~monthly releases tracking Node (Python
v1.60.0, 2026-05-18), Python 3.9–3.13. The Python package is a client to a
bundled Node driver. No disqualifiers found.

## What comes free

- Actionability auto-waiting + retrying web-first assertions (kills most
  timing flake; latency cliffs partially absorbed at the action level).
- Programmatic login + `storage_state` save/restore (cookies, localStorage,
  IndexedDB — **not sessionStorage**; evaluate/init-script workaround needed).
  Credentials stay out of any LLM-visible surface.
- Tracing (`trace.zip`): per-action before/after DOM snapshots, screenshots,
  network bodies, console — strong replay evidence. **PHI-dense by
  construction** (screenshots + response bodies); no built-in redaction; must
  be stored under medical-record-grade controls. HAR has PHI-reduction knobs
  (`minimal`/`omit` content modes); HAR/video flush only at context close
  (crash loses them; chunked tracing via `start_chunk`/`stop_chunk`).
- `route()` can implement default-deny egress, but leaks: service workers
  (mitigate `service_workers="block"`), WebSockets, worker requests,
  browser-internal traffic. Per-context proxy supported → authoritative
  allowlist belongs at the network/container layer; `route()` is
  defense-in-depth + audit signal.
- Browser survives client disconnect: `connect_over_cdp` reattaches to a
  running Chromium (lower fidelity; Chromium-only) — driver process can die
  and reconnect without re-login. Playwright-protocol contexts are cleaned up
  on disconnect (#4467); full-fidelity `launch_server` is Node-only (sidecar
  `playwright run-server` workaround).
- Hardened official Docker images (`mcr.microsoft.com/playwright/python`,
  amd64 + arm64; `--init`, `--ipc=host`, seccomp profile guidance).

## Driver must build (gap list)

1. storage_state custody — it is a bearer credential (encrypt, TTL, never in
   traces/checkpoints)
2. Session-death detection + re-auth loop (auth probe, login-redirect detect)
3. Structured audit log — tamper-evident, PHI-minimal; traces are replay
   evidence, not the audit record
4. Authoritative egress enforcement at network layer
5. Step-level retry/idempotency semantics (post-condition verification)
6. Checkpoint/resume orchestration (chunked traces, periodic state snapshots,
   CDP-sidecar topology)
7. Failure classification (one `TimeoutError` class → dead-session vs latency
   vs DOM-drift discrimination is driver logic)
8. Resource governance (no official sizing; community ~200–600 MB per
   Chromium; version-specific memory regressions exist — pin + benchmark)
