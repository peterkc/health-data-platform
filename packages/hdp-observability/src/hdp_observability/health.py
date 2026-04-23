"""FastAPI health / readiness endpoint factories.

``healthz`` is liveness: the process is up. ``readyz`` is readiness: all
declared dependencies (DB, Mongo, outbox queue, ...) are reachable. Each
service registers its own readiness checks via ``register_readiness_check``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter

ReadinessCheck = Callable[[], Awaitable[bool]]


def register_readiness_check(name: str, check: ReadinessCheck) -> None:
    """Register a readiness probe. Called during service startup."""
    raise NotImplementedError("M3 implementation — see package README TODO.")


def health_router() -> APIRouter:
    """Return an APIRouter exposing GET /healthz and GET /readyz."""
    raise NotImplementedError("M3 implementation — see package README TODO.")
