# Security Policy

## Project Status

This repository is a **reference architecture**, not a production deployment.
It demonstrates platform design for health data systems; it is not operated
as a service and does not process real data.

## No Protected Health Information

No real patient data exists anywhere in this repository or its history. All
fixtures, seeds, and examples are synthetic. The local development stack
(`docker-compose.yml`) uses throwaway dev-only credentials and is not
hardened for exposure beyond localhost.

If you intend to adapt this architecture for systems that handle PHI, you are
responsible for your own HIPAA/regulatory compliance review — nothing here
constitutes a compliant deployment.

## Reporting a Vulnerability

Use GitHub's private vulnerability reporting on this repository
(**Security → Report a vulnerability**). Reports are triaged on a
best-effort basis. Please do not open public issues for security findings.

## Supported Versions

Only the `main` branch is maintained.
