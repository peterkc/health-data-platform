"""Data-model contracts for emr-sync-driver (design stubs — fields, no logic).

Contract SoT for the tracer phases; src/emr_sync_driver/models.py implements
these shapes. reference/audit-event.golden.json MUST validate against
AuditEvent (create-gate C2).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FailureClass(StrEnum):
    """Classification assigned BEFORE any retry decision (FR-007)."""

    DEAD_SESSION = "dead-session"
    LATENCY = "latency"
    SELECTOR_DRIFT = "selector-drift"
    UNKNOWN = "unknown"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    HALTED = "halted"  # clean stop awaiting human decision (e.g. unrecovered drift)


class ActionOutcome(StrEnum):
    OK = "ok"
    FAILED = "failed"
    BLOCKED = "blocked"  # egress allowlist denial (FR-008)


class Job(BaseModel):
    """A sync job; one DBOS workflow execution (FR-003/FR-004)."""

    job_id: str = Field(description="DBOS workflow id; idempotency root")
    workflow: str = Field(description="Workflow name, e.g. 'field-roundtrip'")
    patient_ref: str = Field(description="Synthetic patient identifier in the sandbox")
    status: JobStatus
    submitted_at: datetime
    completed_at: datetime | None = None


class AuditEvent(BaseModel):
    """One browser action; append-only, replayable in order (FR-005).

    MUST NOT contain credentials or storage_state content (FR-009).
    """

    job_id: str
    step_id: str = Field(description="DBOS step name + ordinal, e.g. 'write-field:3'")
    seq: int = Field(ge=0, description="Monotonic per-job sequence number")
    at: datetime
    action: str = Field(description="Verb + target, e.g. 'fill #form_diagnosis'")
    locator: str | None = Field(default=None, description="Selector used, if any")
    outcome: ActionOutcome
    failure_class: FailureClass | None = None
    idempotency_key: str | None = Field(
        default=None, description="Present on write actions (FR-004)"
    )


class SelectorEntry(BaseModel):
    """One named control in the versioned selector map (validated load, NFR-002)."""

    name: str = Field(description="Stable logical name, e.g. 'login.username'")
    selector: str = Field(description="CSS/Playwright selector")
    notes: str | None = None


class SelectorMap(BaseModel):
    emr: str = Field(description="Target EMR product, e.g. 'openemr'")
    emr_version: str = Field(description="Pinned version the map was authored against")
    entries: list[SelectorEntry]


class JobSubmission(BaseModel):
    """POST /jobs request body (FR-006)."""

    workflow: str
    patient_ref: str
