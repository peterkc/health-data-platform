"""LLM-call observability wrapper.

LLMCallTracer wraps a single model invocation so that every call emits a span
with attributes for model name, prompt token count, completion token count,
total latency, and cost estimate. Designed for hh-scribe extraction and
hdp-agent pipelines; abstracted so provider-specific details (OpenAI vs
Anthropic vs local) stay out of callers.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any


class LLMCallTracer(AbstractContextManager["LLMCallTracer"]):
    """Context manager that emits an OTel span around an LLM call.

    Attributes captured:
      - ``llm.vendor`` (openai | anthropic | local | ...)
      - ``llm.model``
      - ``llm.prompt_tokens`` / ``llm.completion_tokens`` / ``llm.total_tokens``
      - ``llm.latency_ms``
      - ``llm.cost_usd`` (best-effort from a static price table)

    Example (post-M3):
        with LLMCallTracer(vendor="openai", model="gpt-4o-mini") as span:
            resp = client.chat.completions.create(...)
            span.record_usage(resp.usage)
    """

    def __init__(self, *, vendor: str, model: str, **extra: Any) -> None:
        self.vendor = vendor
        self.model = model
        self.extra = extra

    def __enter__(self) -> LLMCallTracer:
        raise NotImplementedError("M3 implementation — see package README TODO.")

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        raise NotImplementedError("M3 implementation — see package README TODO.")

    def record_usage(self, usage: Any) -> None:
        """Populate prompt/completion/total token counters from a provider usage object."""
        raise NotImplementedError("M3 implementation — see package README TODO.")
