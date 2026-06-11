# hh-scribe

Transcript -> OASIS item extraction pipeline (LLM-backed).

**Depth**: SKEL

- oasis: OASIS-E2 data model + Pydantic with confidence/citation fields.
- skills: Claude Code skills wrapping MCP tools (SKILL.md + connectors).
- mcp: MCP server exposing home-health scribe + HITL + sync as tools.

TODO: Wire one real LLM call: transcript -> 5 extracted OASIS items.
