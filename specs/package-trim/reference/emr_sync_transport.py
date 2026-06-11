"""Seam contract for hh-emr-sync — lands as `hh_emr_sync.transport` (FR-006).

Transport-agnostic by construction: signatures carry only stdlib / domain types,
never transport-specific ones (no httpx, no playwright). An HTTP-API adapter and
a browser-automation adapter (GH #14/#18, separate driver repository) must both
satisfy this Protocol unchanged — interchangeability is AC-005's subject.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SyncResult:
    """Outcome of one write-back attempt; idempotency key enables safe retry."""

    record_id: str
    idempotency_key: str
    accepted: bool
    detail: str | None = None


@runtime_checkable
class EmrSyncTransport(Protocol):
    """One EMR sync transport (HTTP API today; automation driver later)."""

    def push(self, record_id: str, payload: dict, idempotency_key: str) -> SyncResult:
        """Write one record to the EMR; MUST be idempotent on idempotency_key."""
        raise NotImplementedError

    def health(self) -> bool:
        """Cheap liveness probe for the transport's session/connection."""
        raise NotImplementedError
