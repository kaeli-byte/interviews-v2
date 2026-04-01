"""Server timing helpers for lightweight request instrumentation."""
from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar, Token
from time import perf_counter
from typing import Iterator


def _round_duration(duration_ms: float) -> float:
    """Normalize timings to the precision used in Server-Timing headers."""
    return round(duration_ms, 2)


class TimingCollector:
    """Accumulates named timings and formats them for response headers."""

    def __init__(self) -> None:
        self._durations: OrderedDict[str, float] = OrderedDict()

    def add_duration(self, name: str, duration_ms: float) -> None:
        current = self._durations.get(name, 0.0)
        self._durations[name] = _round_duration(current + duration_ms)

    def as_dict(self) -> dict[str, float]:
        return dict(self._durations)

    def as_header(self) -> str:
        return ", ".join(f"{name};dur={duration:.2f}" for name, duration in self._durations.items())


_current_collector: ContextVar[TimingCollector | None] = ContextVar("timing_collector", default=None)


def get_current_collector() -> TimingCollector | None:
    return _current_collector.get()


def set_current_collector(collector: TimingCollector | None) -> Token:
    return _current_collector.set(collector)


def reset_current_collector(token: Token) -> None:
    _current_collector.reset(token)


@contextmanager
def timing_span(name: str) -> Iterator[None]:
    """Measure a code block and add its duration to the active collector."""
    collector = get_current_collector()
    start = perf_counter()
    try:
        yield
    finally:
        if collector is not None:
            collector.add_duration(name, (perf_counter() - start) * 1000.0)
