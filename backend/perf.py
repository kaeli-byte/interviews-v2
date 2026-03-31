"""Request-scoped performance timing helpers."""
from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar, Token
from time import perf_counter
from typing import Iterator, Optional


_current_collector: ContextVar[Optional["TimingCollector"]] = ContextVar("timing_collector", default=None)


class TimingCollector:
    """Collect named durations and format them for the Server-Timing header."""

    def __init__(self) -> None:
        self._durations_ms: "OrderedDict[str, float]" = OrderedDict()

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        start = perf_counter()
        try:
            yield
        finally:
            self.add_duration(name, (perf_counter() - start) * 1000)

    def add_duration(self, name: str, duration_ms: float) -> None:
        self._durations_ms[name] = self._durations_ms.get(name, 0.0) + max(duration_ms, 0.0)

    def as_dict(self) -> dict[str, float]:
        return {name: round(duration, 2) for name, duration in self._durations_ms.items()}

    def as_header(self) -> str:
        return ", ".join(f'{name};dur={duration:.2f}' for name, duration in self._durations_ms.items())


def set_current_collector(collector: Optional[TimingCollector]) -> Token:
    """Bind a collector to the current async context."""
    return _current_collector.set(collector)


def reset_current_collector(token: Token) -> None:
    """Reset the current async context collector."""
    _current_collector.reset(token)


def get_current_collector() -> Optional[TimingCollector]:
    """Return the collector bound to the current async context, if any."""
    return _current_collector.get()


@contextmanager
def timing_span(name: str) -> Iterator[None]:
    """Measure a named span when a request collector is available."""
    collector = get_current_collector()
    if collector is None:
        yield
        return
    with collector.span(name):
        yield
