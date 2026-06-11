"""Smoke test — replaced once real behavior lands."""

import hdp_core.outbox


def test_smoke() -> None:
    assert hdp_core.outbox
