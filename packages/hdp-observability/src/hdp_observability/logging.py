"""Structured logging via structlog.

configure_logging() is the single entry point every HDP service should call at
startup. In dev it emits human-friendly coloured output; in prod it emits a
JSON line per event so that logs are trivially indexable by Loki/CloudWatch.

Context binding (request_id, tenant_id, clinician_id) will be attached via a
contextvars-backed processor once the API middleware lands in hdp-api.
"""

from __future__ import annotations

from typing import Literal

LogRenderer = Literal["json", "pretty"]


def configure_logging(
    *,
    level: str = "INFO",
    renderer: LogRenderer | None = None,
    service_name: str | None = None,
) -> None:
    """Initialise structlog for the calling process.

    Args:
        level: Root log level (DEBUG/INFO/WARNING/ERROR).
        renderer: Force ``"json"`` or ``"pretty"``. Defaults to pretty when
            stdout is a TTY, json otherwise.
        service_name: Value bound as ``service.name`` on every log record; also
            emitted as the OTel resource attribute once tracing is wired.

    Raises:
        NotImplementedError: Body ships with M3 service integration.
    """
    raise NotImplementedError("M3 implementation — see package README TODO.")
