"""OpenTelemetry meter factory + counter/histogram helpers.

Histograms used by HDP services (ingest latency, scribe extraction latency,
outbox drain lag) will be declared here once those call sites exist.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opentelemetry.metrics import Counter, Histogram, Meter


def meter(name: str = "hdp") -> Meter:
    """Return a named OTel meter, configuring the global provider on first call."""
    raise NotImplementedError("M3 implementation — see package README TODO.")


def counter(name: str, *, description: str = "", unit: str = "1") -> Counter:
    """Create a counter on the default meter."""
    raise NotImplementedError("M3 implementation — see package README TODO.")


def histogram(name: str, *, description: str = "", unit: str = "ms") -> Histogram:
    """Create a histogram on the default meter (default unit: milliseconds)."""
    raise NotImplementedError("M3 implementation — see package README TODO.")
