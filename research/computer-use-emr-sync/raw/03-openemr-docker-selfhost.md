# Source 03 — OpenEMR Docker self-hosting docs

- **Tool**: WebFetch
- **URL**: https://github.com/openemr/openemr/blob/master/DOCKER_README.md
- **Date**: 2026-06-11
- **Provenance**: ai-found

## Findings

- Official images on Docker Hub (`openemr/openemr`): production images tagged
  by version (e.g. `7.0.3`, `latest` = most recent stable); development images
  are the `flex` series plus `dev`/`next` nightlies.
- Compose flavors: production (`docker/production/docker-compose.yml`, also
  runs on arm64/Raspberry Pi), "easy dev" (per CONTRIBUTING.md), and
  "insane dev" multi-service (`docker/development-insane/`).
- Production setup is `docker compose up`, "about 5-10 minutes to complete."
- `flex` series cautioned against production use.
- Docs gap: default ports/credentials and synthetic-data loading are not in
  DOCKER_README.md — resolve from the Docker Hub page / compose files at
  spike time.

## Implication for sandbox selection

Self-hosting is low-friction (single compose file, version-pinned, arm64-capable
— runs on local dev hardware). A pinned version eliminates the drift a shared
demo introduces, and we control reset timing, seeded synthetic patients, and
network isolation.
