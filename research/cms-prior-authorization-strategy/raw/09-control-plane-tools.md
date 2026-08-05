# S-009: Gortex, Pulumi, and Pydantic AI

Source: Gortex exact revision; Context7 Pulumi and Pydantic AI documentation
Tools: WebFetch and Context7
Query: Classify the named tools as runtime, control plane, or development tooling.
Worker: research-worker-terra
Invocation route: task
Revision: gortex@8377da58138d01c9dfa24a1aaf648085ccf0315c; Pulumi current at capture; Pydantic AI v2.0.0
Evidence goal: Establish the architectural boundary for engineering and infrastructure tools named in the source note.
Rationale: Supporting tools must not be mislabeled as healthcare runtime primitives.
Captured: 2026-08-05
Byte verification: verified
Verified by: openai/gpt-5.6-sol primary at 2026-08-05T14:47:00Z
Verification method: Reopened exact Gortex revision files with Exa and reran both approved Context7 queries against exact library IDs.
Normalization: none
Citation verification:
- Source locator: Gortex revision 8377da, README.md, docs/architecture.md, docs/mcp.md
  Source span: README subtitle beginning `Indexes code into graph`
  Capture span: line 72
  Source span SHA-256: 71e3aaf1d120a5851fcb5d79b793d712b97bb6f195af05b9451055e3ef3c46aa
  Capture span SHA-256: 71e3aaf1d120a5851fcb5d79b793d712b97bb6f195af05b9451055e3ef3c46aa
- Source locator: Context7 /pulumi/docs, `pulumi.automation.Stack`
  Source span: exact class description beginning `Stack is an isolated`
  Capture span: line 76
  Source span SHA-256: 50ba306f118497be0bf2cf34830891fe63db861a3ba2c53dd01b1ece9eb4a198
  Capture span SHA-256: 50ba306f118497be0bf2cf34830891fe63db861a3ba2c53dd01b1ece9eb4a198
- Source locator: Context7 /pydantic/pydantic-ai/v2.0.0, AG-UI approval-required tool example
  Source span: exact code line `@agent.tool_plain(requires_approval=True)`
  Capture span: line 80
  Source span SHA-256: d77c6b7dc9924a8520ae1418d8aaa55cd86b184e71bd3b13832b095fd367fd89
  Capture span SHA-256: d77c6b7dc9924a8520ae1418d8aaa55cd86b184e71bd3b13832b095fd367fd89
Outcome: gathered

## Evidence

### Gortex

Gortex is an Apache-2.0 code-intelligence system for agents and IDEs. It indexes
repositories into an in-memory graph, persists local snapshots, and exposes
navigation, analysis, review, and guarded source-edit operations over CLI, MCP,
HTTP, and UI. Read-only and navigation-only tool presets exist, but mutability is
configuration-dependent.

Verdict boundary: development tooling, not an HDP runtime or health-data store.

### Pulumi

Pulumi Automation API exposes stack configuration and the full infrastructure
lifecycle: preview, update, refresh, destroy, outputs, secret-marked config, and
programmatic testing. A caller can invoke deployment directly; approval,
separation of duties, change windows, and policy gates belong in the surrounding
controller and cloud/IAM design.

Verdict boundary: deployment/control plane. It is useful when the OSS project has
a real deployable service, not a core authorization dependency.

### Pydantic AI

Pydantic AI v2 supports typed tools, deferred calls, explicit approval-required
tools, host-provided results, Temporal and Restate durable-execution wrappers,
and model/tool tracing through Logfire. The host application still creates and
executes external work, approves or denies consequential calls, persists audit
records, and resumes the agent with bounded results.

Verdict boundary: optional application-level agent framework. It can support
drafting, triage, or explanation after deterministic case and evidence logic
exists; it is not the policy authority or side-effect controller.

## Verified Excerpts

```text
Indexes code into graph and exposes it via CLI, MCP Server, and web UI. Multi-repository support by default.
```

```text
Stack is an isolated, independently configurable instance of a Pulumi program. It exposes methods for the full pulumi lifecycle (up/preview/refresh/destroy), as well as managing configuration.
```

```python
@agent.tool_plain(requires_approval=True)
```

## Notes

For the first OSS tracer, Gortex can improve development and Pydantic AI can be
kept behind an optional adapter. Pulumi should be deferred until deployment is
real. None belongs in the domain model or should be required to validate an
authorization evidence packet.

## Followups

- Add IaC only when the project deploys a service with state and operational
  gates.
- Add an agent only after deterministic behavior and review boundaries have
  complete tests.
