"""Observability.

An agent you cannot see is an agent you cannot operate. Every meaningful step
emits a structured span: what happened, with what inputs/outputs, and how long
it took. Spans are emitted as JSON lines so they drop straight into any log
pipeline (Cloud Logging, OpenTelemetry collectors, etc.).

Time is injected (``clock``) so traces are deterministic in tests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from itertools import count
from typing import Callable


@dataclass
class Span:
    id: int
    name: str
    attributes: dict
    duration_ms: float


class Tracer:
    def __init__(self, clock: Callable[[], float] | None = None, sink: Callable[[str], None] | None = None) -> None:
        # Deterministic default clock advances 1ms per read -> stable test output.
        self._tick = count()
        self._clock = clock or (lambda: float(next(self._tick)))
        self._sink = sink or (lambda line: None)
        self.spans: list[Span] = []
        self._ids = count(1)

    def span(self, name: str, **attributes) -> "_SpanCtx":
        return _SpanCtx(self, name, attributes)

    def _record(self, name: str, attributes: dict, duration_ms: float) -> Span:
        span = Span(id=next(self._ids), name=name, attributes=attributes, duration_ms=duration_ms)
        self.spans.append(span)
        self._sink(json.dumps({"span": name, "duration_ms": duration_ms, **attributes}))
        return span

    def _now(self) -> float:
        return self._clock()


@dataclass
class _SpanCtx:
    tracer: Tracer
    name: str
    attributes: dict = field(default_factory=dict)
    _start: float = 0.0

    def __enter__(self) -> "_SpanCtx":
        self._start = self.tracer._now()
        return self

    def set(self, **attrs) -> None:
        self.attributes.update(attrs)

    def __exit__(self, *exc) -> None:
        duration = self.tracer._now() - self._start
        self.tracer._record(self.name, self.attributes, duration)
