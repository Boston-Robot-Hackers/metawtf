#!/usr/bin/env python3
"""metawtf.rate_counter: rolling-window message rate from arrival times.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from collections import deque


class RateCounter:
    """Span-based rate estimator over a rolling time window.

    Rate is (n-1)/(t_newest - t_oldest) across the arrivals still inside the
    window, matching `ros2 topic hz`. Unlike count/window it does not
    under-report at startup or for sparse topics. The clock is injected: callers
    pass a monotonic `now` to `record` and `rate`.
    """

    def __init__(self, window: float):
        self.window = window
        self.arrivals = deque()

    def record(self, now: float) -> None:
        self.arrivals.append(now)

    def prune(self, now: float) -> None:
        cutoff = now - self.window
        while self.arrivals and self.arrivals[0] < cutoff:
            self.arrivals.popleft()

    def rate(self, now: float) -> float | None:
        self.prune(now)
        if len(self.arrivals) < 2:
            return None
        span = self.arrivals[-1] - self.arrivals[0]
        if span <= 0:
            return None
        return (len(self.arrivals) - 1) / span
