# Health Data Platform (HDP)

[![CI](https://github.com/peterkc/health-data-platform/actions/workflows/test.yml/badge.svg)](https://github.com/peterkc/health-data-platform/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)

**AI-native workflow and governance layer for healthcare verticals.**

HDP takes clinical documentation from ambient capture through structured
assessment and human-in-the-loop review to EMR write-back, with the consent,
provenance, and audit primitives those workflows demand. Home health is the
first vertical: OASIS-E assessments drafted by an LLM scribe, gated through
confidence-aware review, and synced to EMRs — including the many that expose
no API. It is a reference architecture under active development; no real
patient data is processed anywhere in this repository, and all fixtures are
synthetic.

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

The platform layer is the governance spine: `hdp-core` carries canonical
domain records with trust level and provenance, grant-based consent with
42 CFR Part 2 fail-closed category semantics, append-only audit, identity
linkage, and outbox primitives alongside the agent runtime whose confidence
scores feed the review queue. The vertical layer owns the
domain: OASIS-E modeled as first-class structured data, a
`suggested → reviewed → accepted/edited/rejected` review state machine with a
finalize gate, and a transport-agnostic EMR adapter contract — HTTP APIs where
they exist, browser-level automation where they don't. Schemas and semantics
are specified in the design corpus below; each package README labels its
implementation depth.

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

The `vault` branch carries the design corpus — table designs (30-table DDL
plan, uuidv7 keys), the consent model, FHIR surface evaluation,
interoperability research, and ADRs:
[browse the vault branch](https://github.com/peterkc/health-data-platform/tree/vault).

## License

[MIT](LICENSE)
