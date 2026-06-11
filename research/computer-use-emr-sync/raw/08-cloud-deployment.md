# Source 08 — Cloud deployment options

Gathered 2026-06-11 via WebSearch/WebFetch: docs.browserbase.com enterprise
security, browserbase.com/enterprise, AWS Fargate/Playwright deployment
guides, dev.to framework-wars survey, DBOS/Temporal durable-execution
comparisons (see also raw/05–07 for per-framework cloud coupling).

## Managed browser infrastructure

- **Browserbase** (the category leader; backs Stagehand): SOC 2 Type II,
  **HIPAA-compliant with BAAs/DPAs available on request**, zero-data-retention
  mode (no logs/recordings/replay persisted), per-session dedicated VM killed
  and recreated after each session, isolated subnets, SSO/SAML, region
  selection. Sources: docs.browserbase.com/account/enterprise/security,
  browserbase.com/enterprise.
- Alternatives in the category (Steel, Hyperbrowser, Anchor) not evaluated in
  depth this pass — Browserbase's compliance posture is the benchmark to
  compare against.

## Self-hosted containers (BAA-covered cloud)

- **ECS Fargate** is the canonical AWS shape for long-running browser jobs:
  no runtime limits (vs Lambda's 15 min), up to 120 GB memory, horizontal
  scaling; official Playwright images from ECR; community sizing ≥1–2 GB per
  browser task, `--no-sandbox` in containers, zombie-process hygiene.
  Equivalents: GCP Cloud Run jobs / GKE, Azure Container Apps.
- AWS/GCP/Azure all sign BAAs covering compute/database/secrets services —
  the self-host path keeps every PHI-touching component inside one BAA
  boundary.
- LLM inference for the assist path can stay inside the same boundary via
  BAA-covered model platforms (e.g., AWS Bedrock serving Anthropic models) —
  resolves the posture gap flagged for vision-assist screenshots.

## Durable execution / checkpoint layer (from prior pass, recorded here)

- **DBOS Transact** (Python, embedded library, Postgres-backed): workflows
  resume from last completed step after crash; completed LLM/tool calls
  replayed from the database, not re-executed; 2026 adds in-flight workflow
  patching. Fits the existing Postgres stack with zero extra services.
- **Temporal**: external cluster, enterprise-scale, migrate-to-if-walls-hit.
  Sources: dbos.dev, tiarebalbi.com DBOS-vs-Temporal, pydantic.dev DBOS
  article, temporal.io.

## EMR-specific constraint

Agency EMR/payer portals frequently allowlist source IPs — egress must
present a static IP (NAT gateway / pinned egress proxy). This cuts against
managed browser fleets with rotating IPs unless the vendor offers dedicated
egress; native in the self-hosted VPC topology.
