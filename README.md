# Health Data Platform (HDP)

[![CI](https://github.com/peterkc/health-data-platform/actions/workflows/test.yml/badge.svg)](https://github.com/peterkc/health-data-platform/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)

**AI-native workflow and governance layer for healthcare verticals** — ambient
capture → structured assessment → human-in-the-loop review → EMR write-back,
with the consent, provenance, and audit primitives those AI workflows demand.

Home health is the first vertical slice: OASIS-E assessments drafted by an LLM
scribe, gated through confidence-aware human review, and synced to EMRs —
including the many that expose no API.

HDP is **not** a FHIR clinical data repository, and doesn't compete with one.
Pair it with a CDR such as [Medplum](https://github.com/medplum/medplum) or
HAPI: HDP is the workflow that fills the CDR and the governance that controls
what leaves it. The canonical record model treats FHIR R4 as a *projection* —
one output among several (IPS, OMOP) — rather than the storage shape. The
build-vs-pair evaluation is recorded in the
[FHIR surface research](https://github.com/peterkc/health-data-platform/blob/vault/research/fhir-surface.md).

## Architecture

Three layers, dependencies pointing strictly downward:

```
+--------------------------------------------------------------+
|  Apps         composed deployables (home-health-scribe)      |
+--------------------------------------------------------------+
|  Verticals    domain workflows: OASIS-E assessment, ambient  |
|               scribe, HITL review, EMR sync                  |
+--------------------------------------------------------------+
|  Platform     canonical records | consent | provenance |     |
|  primitives   audit | identity | ingest | agent runtime      |
+--------------------------------------------------------------+
         FHIR R4 / IPS / OMOP are projections, not storage
```

## Platform primitives

| Primitive | Owns | Status |
|---|---|---|
| **Canonical** | Domain records with trust level + provenance; FHIR R4-first vocabulary, storage-shape independent | designed |
| **Consent** | Grant-based access with 42 CFR Part 2 fail-closed category semantics — `categories: NULL` means non-sensitive only | designed |
| **Provenance** | Who/what/when column discipline on every record | designed |
| **Audit** | Append-only event trail | designed |
| **Identity** | Patient/practitioner identity and linkage | designed |
| **Ingest** | Source adapters into canonical records | designed |
| **Agent runtime** | LLM execution with confidence scoring feeding HITL | designed |
| **Observability** | OTel tracing for LLM calls, structured logging, health checks | interfaces typed |

*"designed" = schema + semantics specified in the
[design research](https://github.com/peterkc/health-data-platform/tree/vault/research);
implementation tracked in the [roadmap](#roadmap). Depth is labeled honestly
per package — see [Status](#status).*

## Home health vertical

The wedge HDP is built to demonstrate:

- **OASIS-E** — the CMS home-health assessment instrument, modeled as
  first-class structured data (not generic questionnaires)
- **HITL review** — `suggested → reviewed → accepted/edited/rejected` state
  machine with a finalize gate; low-confidence extractions cannot skip review
- **EMR sync** — transport-agnostic adapter contract; HTTP APIs where they
  exist, browser-level automation where they don't
  ([roadmap epic](https://github.com/peterkc/health-data-platform/issues/14))

## Quickstart

```bash
git clone https://github.com/peterkc/health-data-platform.git
cd health-data-platform
just up       # Postgres 18 (pgvector) + Mongo 7; bootstraps .env on first run
just verify   # lint + tests (CI mirror)
```

`just dev` (the composed home-health-scribe app) lands with the
[make-it-run epic](https://github.com/peterkc/health-data-platform/issues/12).

## Design research

The `vault` branch carries the project's design corpus — table designs
(30-table DDL plan, uuidv7 keys), the consent model, FHIR surface
evaluation, interoperability research, and ADRs:
[browse the vault branch](https://github.com/peterkc/health-data-platform/tree/vault).

## Roadmap

Built in public; the epic chain is the plan:

1. [#5 — OSS release readiness](https://github.com/peterkc/health-data-platform/issues/5)
2. [#11 — package consolidation](https://github.com/peterkc/health-data-platform/issues/11)
3. [#12 — make it run: app + schema](https://github.com/peterkc/health-data-platform/issues/12)
4. [#13 — domain depth: OASIS, HITL, scribe](https://github.com/peterkc/health-data-platform/issues/13)
5. [#14 — computer-use EMR automation (research first)](https://github.com/peterkc/health-data-platform/issues/14)

## Status

Reference architecture under active development, designed primitives-first.
Package READMEs carry explicit depth markers (`DEEP / MIN / SKEL / COMPOSED`)
so the implemented-vs-designed boundary is always visible. No real patient
data is processed anywhere in this repository — all fixtures are synthetic.
See [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
