#!/usr/bin/env python3
"""metawtf.hz_column: per-topic sampled state for an `hz` column.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from metawtf.config import sanitize_topic
from metawtf.rate_counter import RateCounter


class HzColumnState:
    """Records message arrivals and reports the rolling receive rate.

    The subscription callback passes the (raw, undeserialized) message; only its
    arrival time matters, so the payload is ignored.
    """

    def __init__(self, name: str, window: float, width: int | None = None):
        self.name = name
        self.width = width
        self.counter = RateCounter(window)

    @classmethod
    def from_topic(cls, topic: str, window: float, width: int | None = None):
        return cls(name=sanitize_topic(topic), window=window, width=width)

    def on_message(self, raw_msg, now: float) -> None:
        self.counter.record(now)

    def sample(self, now: float) -> str | None:
        rate = self.counter.rate(now)
        if rate is None:
            return None
        return f"{rate:.2f}"
