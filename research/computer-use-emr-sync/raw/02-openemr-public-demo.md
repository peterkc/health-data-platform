# Source 02 — OpenEMR public demo page

- **Tool**: WebFetch
- **URL**: https://www.open-emr.org/demo/
- **Date**: 2026-06-11
- **Provenance**: ai-found

## Findings

- Three identical public demo installations: `demo.openemr.io/openemr`,
  `/a/openemr`, `/b/openemr`; separate patient-portal demos at `/portal` paths.
- Role-based logins published on the page (admin/pass, physician/physician,
  clinician/clinician, accountant, receptionist; portal patients Phil1/phil,
  Susan2/susan).
- **Reset cadence: wiped daily, "reset overnight (8:00 am UTC time)"** — no
  entered data persists between sessions.
- Pre-loaded synthetic configuration for demonstrating billing, accounting,
  access controls, portal; only the two named portal patients are guaranteed
  synthetic-patient data.
- **No explicit terms or acceptable-use policy is stated** for the demo.

## Implication for sandbox selection

The daily wipe destroys multi-day failure-taxonomy state; the instances are
shared (other visitors' actions confound observed failures); and the absence
of an AUP cuts both ways — nothing forbids automation, but nothing authorizes
sustained automated traffic against community-funded infrastructure either.
Useful for quick manual UI recon; wrong substrate for spike runs.
