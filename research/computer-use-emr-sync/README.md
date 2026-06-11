---
id: computer-use-emr-sync
title: Computer-use as an EMR sync transport
type: research
status: proposed
created: 2026-06-11
updated: 2026-06-11
hub: computer-use-emr-sync
parent_hub: null
owner: peterkc
audience: [driver-repo implementers, hh-emr-sync adapter design]
direction: exploring
tags: [computer-use, emr-sync, security, sandbox, home-health]
related: []
---

# Computer-use as an EMR sync transport

Living hub for GitHub #18 (parent epic #14). Accrues alongside the driver
spike — a record, not a gating phase.

## Situation

Many EMR systems serving home health expose weak or no integration APIs.
`hh-emr-sync` today declares only `httpx` as its transport dependency,
presuming an API that many target systems lack (GH #14). OpenEMR is already
known to this vault as a schema-design reference [ai-found: raw/01]; here it
reappears in a different role — a real EMR UI to automate against.

## Complication

Browser-level automation (DOM-driven, vision-assisted) is a credible
additional transport for API-poor targets, but credentialed browser sessions
against a medical-records UI carry a threat model that HTTP clients do not:
prompt injection from rendered content, credential exposure, and a long tail
of workflow failure modes (session death, selector drift, latency cliffs,
partial write-back). The driver must be credible *infrastructure*, not a demo.

## Question

What does a browser-level EMR sync transport need to be credible
infrastructure: how are credentialed sessions secured, which sandbox grounds
the work, and how do long-running browser workflows against EMR UIs actually
fail?

## Approach

Four sources gathered 2026-06-11 (see `state.yaml` for the plan): prior vault
context, the OpenEMR public demo page, OpenEMR Docker self-hosting docs, and
Anthropic's computer-use security/limitations documentation. The failure
taxonomy below is a seed structure — its rows accrue from tracer-spike runs in
the driver repository, each observed class feeding retry/idempotency/
observability design.

## Findings

### Security posture

Grounded in the vendor's own guidance for computer-use agents
[ai-found: raw/04]:

1. **Synthetic data only.** The sandbox holds zero real patient data, ever.
   This is scope, not mitigation — there is no failure mode in which PHI is
   exposed because no PHI exists in the loop.
2. **Container isolation, minimal privileges.** The driver and the browser it
   controls run in a dedicated container/VM ("dedicated virtual machine or
   container with minimal privileges" — raw/04). The Anthropic reference
   implementation itself is Docker-contained.
3. **Network allowlist.** The browser environment can reach the sandbox EMR
   and nothing else ("limiting internet access to an allowlist of domains" —
   raw/04). An injected instruction cannot exfiltrate to a host it cannot
   resolve.
4. **Credentials outside the model loop.** DOM-first automation performs
   login programmatically (selectors + secret store), so credentials never
   enter a prompt. The vendor path of last resort — credentials in prompt XML
   tags — is documented to increase prompt-injection blast radius (raw/04);
   the DOM-first default avoids it structurally.
5. **Session/audit boundary.** Every driver action that mutates EMR state is
   logged as an auditable event; write-back operations carry idempotency keys
   so a replay after partial failure cannot double-apply. This is where the
   driver meets HDP's audit/provenance primitives.
6. **HITL gates on consequential writes.** Human confirmation before
   meaningful real-world consequences (raw/04) aligns with HDP's existing
   confidence-gated HITL design — the transport inherits the platform's
   review checkpoint rather than inventing its own.
7. **Prompt-injection stance.** Rendered EMR content is untrusted input.
   Defense in depth: DOM-first control (the model is not steering from
   screenshots in the default path), Anthropic's screenshot classifiers when
   vision assist is active, allowlisted egress, and HITL gates — the docs are
   explicit that precautions remain necessary even with the classifier layer
   (raw/04).

### Sandbox selection — self-hosted OpenEMR (decision)

**Decision: self-hosted OpenEMR via the official Docker production compose,
version-pinned.** [ai-found: raw/02, raw/03]

| Criterion | Public demo (`demo.openemr.io`) | Self-hosted Docker |
| --- | --- | --- |
| State persistence | Wiped daily at 8:00 UTC | We control reset timing |
| Isolation | Shared with other visitors | Single-tenant |
| Authorization for automated traffic | No AUP stated either way | Our infrastructure |
| Version stability | Tracks upstream | Pinned (e.g. `7.0.3`) |
| Synthetic patients | Two portal patients guaranteed | Seeded deliberately |
| Setup cost | Zero | `docker compose up`, ~5-10 min, arm64-capable |

The daily wipe alone disqualifies the public demo for failure-taxonomy work —
multi-day observation of session death and drift requires state we own. The
demo remains useful for quick manual UI recon. Gap to resolve at spike time:
default ports/credentials and synthetic-data loading live in the Docker Hub
page/compose files, not DOCKER_README.md (raw/03).

### DOM-first, vision-assist (decision)

**Decision: DOM-driven automation is the primary control loop; vision is
assist and fallback.** The vendor's own limitation list argues for this
[ai-found: raw/04]: latency "too slow compared to regular human-directed
computer actions," coordinate hallucination in vision-driven clicking,
scrolling unreliability, and degraded reliability against niche applications
— EMR UIs being exactly that. DOM selectors are deterministic, fast, cheap,
and auditable (a selector either matched or it didn't; a logged action replay
is exact). Vision assist earns its place where the DOM fails: canvas-rendered
or legacy widgets, selector-drift recovery (visually re-locating a control
whose selector broke), and CAPTCHAs-class anomalies that should halt for human
review anyway.

### Failure taxonomy (seed)

Classes named in #18; rows accrue from spike runs in the driver repo. Each
observed failure gets: detection signal, blast radius, hardening
recommendation.

| Class | What it looks like | Hardening direction (hypothesis) |
| --- | --- | --- |
| Session death | Auth timeout/logout mid-workflow | Checkpointed orchestration; re-auth + resume from last checkpoint |
| Selector drift | EMR update changes DOM; selectors stop matching | Versioned selector maps; vision-assisted re-location; drift alarms |
| Latency cliffs | Page loads stall; waits time out unpredictably | Adaptive timeouts; circuit breakers; observability on wait distributions |
| Partial write-back | Multi-field form submit interrupted midway | Idempotency keys; read-after-write verification; transactional batching where the UI allows |

The infrastructure interest is in this column structure — retries,
idempotent write-back, checkpointed orchestration, observability — more than
in any single extraction's accuracy.

## Synthesis

A credible browser-level EMR sync transport is **a hardened, audited,
DOM-first driver running against owned, synthetic-only infrastructure** — not
a vision-loop agent pointed at a shared demo. The security posture is mostly
structural (isolation, allowlist, credentials outside the model loop,
synthetic-only scope) rather than behavioral, which is what makes it
defensible. The sandbox decision (self-hosted, pinned OpenEMR) follows from
needing multi-day failure state; the DOM-first decision follows from the
vendor's own limitation list. What remains genuinely open — how these
workflows fail in practice — is empirical, and the taxonomy table is the
instrument for capturing it.

Adapter-contract implications for the `hh-emr-sync` seam (#11): the contract
must accommodate idempotency keys, checkpoint/resume semantics, and
asynchronous completion — an HTTP adapter satisfies these trivially; an
automation adapter requires them. If the seam bakes in synchronous
request/response, the automation transport will not slot in.

## Open questions

- Driver repository: name and visibility (pending owner decision); hub links
  out once created.
- OpenEMR synthetic-patient seeding: best mechanism (built-in demo data vs
  Synthea import) — resolve at spike time.
- Default ports/credentials for the production compose — Docker Hub page.
- Which OASIS-relevant OpenEMR workflows make the first tracer target (visit
  documentation? assessment forms?).

## Next actions

- Create the driver repository; first tracer run against self-hosted OpenEMR.
- Begin populating taxonomy rows from observed failures (one hardening
  recommendation per observed class — #18 exit condition).
- Feed adapter-contract implications into the #11 trim spec's emr-sync seam.

## Cross-references

- `state.yaml` — structured state for AI re-load
- `raw/` — per-source captures (01 vault context, 02 demo page, 03 Docker
  docs, 04 Anthropic security)
- GitHub: #18 (this spike), #14 (parent epic), #11 (adapter seam)
- `../references.md` #9 — OpenEMR as schema reference (distinct role)
