# Source 01 — Prior vault context (local grep)

- **Tool**: grep across `vault/research/*.md`
- **Date**: 2026-06-11
- **Provenance**: ai-found

## Findings

- OpenEMR is already a known reference: `references.md` #9 lists it as a
  "traditional open source EHR (provider-centric). Useful for clinical workflow
  shapes; less applicable to patient-owned model."
- `design-lessons.md` includes OpenEMR in the cross-schema comparison set
  (FHIR, OMOP, openEHR, i2b2, Fasten, HealthKit, OpenEMR/OpenMRS, USCDI) and
  rejects its provider-centric identity pattern for HDP's own schema.
- No prior vault artifact covers computer-use, browser automation, or sync
  transports. This hub is the first.

## Implication

OpenEMR's role here is different from its earlier appearance: previously a
schema-design reference, now a **sandbox target** — a real EMR UI to drive
against. No conflict between the two uses.
