"""CLI contract for emr-sync-driver (design stubs — signatures + exit contracts, no behavior).

Contract SoT for the tracer phase; src/emr_sync_driver/cli.py implements it.
All commands: exit 0 on success; exit 1 on classified job failure; exit 2 on
usage/config error (typed, no traceback — NFR-002).
"""

from __future__ import annotations

import typer

app = typer.Typer(name="emr-sync", no_args_is_help=True)
audit_app = typer.Typer(name="audit", no_args_is_help=True)
app.add_typer(audit_app)


@app.command()
def run(
    workflow: str = typer.Argument(..., help="Workflow name, e.g. 'field-roundtrip'"),
    patient: str = typer.Option(..., "--patient", help="Synthetic patient ref in the sandbox"),
    fallback: bool = typer.Option(False, "--fallback", help="Enable drift-recovery seam (FR-010); default deterministic-only"),
) -> None:
    """Submit and run a sync job to completion (FR-003).

    Output: job id + terminal status on stdout (one line, parseable).
    Exit: 0 succeeded; 1 failed/halted (classification printed); 2 bad args/config.
    """
    raise NotImplementedError


@app.command()
def resume(
    job_id: str = typer.Argument(..., help="Job to resume from last completed checkpoint"),
) -> None:
    """Resume a dead job; completed writes are not re-applied (FR-004).

    Exit: 0 job completed; 1 job failed again (classification printed);
    2 unknown job id (typed error).
    """
    raise NotImplementedError


@app.command()
def status(
    job_id: str = typer.Argument(..., help="Job to inspect"),
) -> None:
    """Print job status + last completed step (FR-006).

    Output: JobStatus value + step id on stdout. Exit: 0; 2 unknown job id.
    """
    raise NotImplementedError


@audit_app.command()
def replay(
    job_id: str = typer.Argument(..., help="Job whose audit log to replay"),
) -> None:
    """Print every audit event of a job, in seq order, one per line (FR-005, AC-005).

    Output: rendered AuditEvent per line (timestamp, step, action, outcome).
    Exit: 0; 2 unknown job id.
    """
    raise NotImplementedError


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8400, "--port"),
) -> None:
    """Serve the thin FastAPI surface (FR-006): POST /jobs, GET /jobs/{id},
    POST /jobs/{id}/resume, /openapi.json.

    Foreground process; exit 2 on bad config (e.g. unreachable DBOS database).
    """
    raise NotImplementedError
