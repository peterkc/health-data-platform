"""OpenTelemetry tracer factory + auto-instrumentation hooks.

The factory defers SDK configuration until first use so that importing this
module in a test context (where no collector is running) is cheap and side
effect free.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer


def tracer(name: str = "hdp") -> Tracer:
    """Return a named OTel tracer, configuring the global provider on first call.

    Raises:
        NotImplementedError: Body ships with M3 service integration.
    """
    raise NotImplementedError("M3 implementation — see package README TODO.")


def instrument_fastapi(app: Any) -> None:
    """Attach the FastAPI ASGI instrumentor to ``app``."""
    raise NotImplementedError("M3 implementation — see package README TODO.")


def instrument_sqlalchemy(engine: Any) -> None:
    """Attach the SQLAlchemy instrumentor to ``engine``."""
    raise NotImplementedError("M3 implementation — see package README TODO.")


def instrument_httpx() -> None:
    """Auto-instrument all httpx clients created in this process."""
    raise NotImplementedError("M3 implementation — see package README TODO.")
