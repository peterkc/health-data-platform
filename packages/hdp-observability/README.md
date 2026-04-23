# hdp-observability

OpenTelemetry + structured logging + health/readiness primitives for HDP services.

## Status — MIN depth

This package ships as a **scaffold**. The public interfaces are fully typed and
documented; the bodies raise `NotImplementedError` and land with M3 service
integration.

- `logging.configure_logging` — structlog bootstrap (json/pretty rendering)
- `tracing.tracer` / `instrument_fastapi` / `instrument_sqlalchemy` / `instrument_httpx`
- `metrics.meter` / `counter` / `histogram`
- `llm.LLMCallTracer` — OTel span wrapper for LLM invocations
- `health.register_readiness_check` / `health_router` — FastAPI `/healthz`, `/readyz`

## Design intent

- Single choke point for every service's structured log bootstrap so that
  `service.name`, `request.id`, `tenant.id`, and `clinician.id` land on every
  record the same way.
- Tracer/meter factories are lazy so importing this package in test context
  (where no collector is running) is free.
- `LLMCallTracer` captures token counts, latency, and a best-effort cost
  estimate on every model invocation — surfaces prompt drift and spend without
  caller-specific plumbing.
- Health/readiness endpoints are a router factory so each service composes its
  own readiness checks.

## TODO (M3)

- Flesh out `configure_logging` with contextvars-backed processors.
- Wire the OTel global tracer/meter providers with batch OTLP exporters; honour
  `OTEL_EXPORTER_OTLP_ENDPOINT`.
- Implement `LLMCallTracer` token accounting (OpenAI + Anthropic usage shapes).
- Readiness registry + async-safe probe execution for `health_router`.

Run the OTLP collector locally with:

```
just observability-up
```
