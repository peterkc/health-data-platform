# S-003: HTI-4 and provider EHR integration

Source: ASTP/ONC HTI-4 overview; GovInfo 90 FR 36536; ASTP/ONC FY2027 update
Tools: Exa web fetch
Query: not applicable
Worker: research-worker-terra
Invocation route: task
Revision: not applicable
Evidence goal: Verify certification criteria, CEHRT linkage, CDS Hooks and subscriptions, dates, and FY2027 guide versions.
Rationale: This determines whether HDP can sit beside an EHR or needs a certified partner.
Captured: 2026-08-05
Byte verification: verified
Verified by: openai/gpt-5.6-sol primary at 2026-08-05T14:36:00Z
Verification method: Reopened all approved URLs with Exa; GovInfo replaced the user-approved blocked FederalRegister.gov route.
Normalization: none
Citation verification:
- Source locator: https://www.govinfo.gov/content/pkg/FR-2025-08-04/html/2025-14681.htm
  Source span: exact text `voluntary certification of health information technology.`
  Capture span: line 62
  Source span SHA-256: 477b884a063fe8772f0e89817fed484c76abe0d9be198ade625ecfc80186f62b
  Capture span SHA-256: 477b884a063fe8772f0e89817fed484c76abe0d9be198ade625ecfc80186f62b
Outcome: gathered

## Evidence

### Certification boundary

- HTI-4 took effect October 1, 2025 and finalizes a limited set of ONC Health IT
  Certification Program changes.
- The program is a voluntary health IT product/module certification program. The
  new API conditions apply when a developer chooses to certify to the applicable
  criteria; the evidence does not say every third-party tool must be certified.
- Medicare Promoting Interoperability and MIPS reporting are provider incentive-
  program obligations. They are distinct from a developer's choice to certify a
  module.

### Criteria and dependencies

- Section 170.315(g)(31), Coverage Requirements Discovery, references CRD and
  cross-references section 170.315(j)(20), the CDS Hooks client criterion.
- Section 170.315(g)(32), Documentation Templates and Rules, references DTR and
  SMART App Launch.
- Section 170.315(g)(33), Prior Authorization Support, references PAS and SMART
  App Launch and cross-references section 170.315(j)(21), the subscriptions
  client criterion.
- The ASTP page contains an apparent editorial error that names (g)(31) in the
  sentence following the (g)(33) subscriptions requirement. Its immediate
  context and the rule summary support (g)(33) to (j)(21), not an additional
  (g)(31) subscription requirement.
- Real-world testing requirements apply after certification. Modules certified
  before August 31, 2026 conduct CY 2027 testing and submit in March 2028.

### Version update

- Effective October 1, 2026, ONC replaces the initial HTI-4 versions with CRD
  2.2.1, DTR 2.2.0, and PAS 2.2.1. The same update adopts CDex 2.1.0 and newer
  payer-data guides.

## Verified Excerpt

```text
voluntary certification of health information technology.
```

## Notes

The intended workflow is EHR-connected, but certification is modular rather than
a blanket requirement on every component. A provider-side OSS component can sit
beside certified health IT if it preserves the certified workflow boundary; it
should not claim incentive eligibility without checking the specific measure and
deployment configuration.

## Followups

- Non-blocking: verify the final 2027 measure specification and exact CEHRT
  configuration before making eligibility claims.
- Report the apparent ASTP cross-reference typo rather than reproducing it.
