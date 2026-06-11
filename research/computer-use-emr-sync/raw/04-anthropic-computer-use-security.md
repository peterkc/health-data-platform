# Source 04 — Anthropic computer-use docs (security + limitations)

- **Tool**: WebFetch
- **URL**: https://platform.claude.com/docs/en/docs/agents-and-tools/computer-use
- **Date**: 2026-06-11
- **Provenance**: ai-found

## Security considerations (quoted/paraphrased)

Recommended precautions:

1. "Using a dedicated virtual machine or container with minimal privileges to
   prevent direct system attacks or accidents."
2. "Avoiding giving the model access to sensitive data, such as account login
   information, to prevent information theft."
3. "Limiting internet access to an allowlist of domains to reduce exposure to
   malicious content."
4. "Asking a human to confirm decisions that might result in meaningful
   real-world consequences."

Prompt injection: "In some circumstances, Claude will follow commands found in
content even if it conflicts with the user's instructions... instructions on
webpages or contained in images might override instructions." Anthropic runs
prompt-injection classifiers on screenshots that steer the model to ask for
user confirmation; the docs note "these precautions remain important even with
the classifier defense layer in place."

Credentialed sessions: if the model must log in, credentials go in the prompt
inside XML tags (e.g. `<robot_credentials>`) — and the docs flag that
"using computer use within applications that require login increases the risk
of bad outcomes as a result of prompt injection."

Reference implementation: Xvfb virtual display + lightweight Linux desktop,
"runs all of this inside a Docker container."

## Stated limitations (numbered in docs)

1. **Latency** — "might be too slow compared to regular human-directed
   computer actions"; suited to background/batch work, not interactive speed.
2. **Vision accuracy** — "might make mistakes or hallucinate when outputting
   specific coordinates."
3. **Tool-selection reliability** — lower against niche applications.
4. **Scrolling reliability** — keyboard alternatives (Page Down) as fallback.
5. **Spreadsheet/fine-grained interaction** — multiple attempts may be needed.
7. **Vulnerabilities** — jailbreak/prompt-injection "might persist across
   frontier AI systems"; limit to trusted VMs/containers, minimal privileges.

Closing guidance: "Do not use Claude for tasks requiring perfect precision or
sensitive user information without human oversight."

## Implication

The vendor's own limitation list (latency, coordinate hallucination, scroll
unreliability) is a direct argument for **DOM-first** automation with vision
as assist/fallback, not the primary control loop. The security list maps
cleanly onto the spike's posture: container isolation, domain allowlist,
synthetic-only data, runtime credential injection, HITL gates on writes.
