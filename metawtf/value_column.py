#!/usr/bin/env python3
"""metawtf.value_column: shared sampled-scalar state for value columns.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

INVALID = object()  # a message arrived but its value could not be read


class ValueColumnState:
    """Common last-known-value, staleness, and formatting for scalar columns.

    Subclasses implement `on_message`, storing either a scalar in `self.value`
    (and `self.arrival_time`) or the `INVALID` sentinel when the message arrived
    but its value could not be extracted. Everything else — empty cell before
    the first message, staleness, "?" for invalid, float formatting — is shared.
    """

    def __init__(self, name: str, stale_after: float | None, width: int | None):
        self.name = name
        self.stale_after = stale_after
        self.width = width
        self.value = None
        self.arrival_time = None

    def is_stale(self, now: float) -> bool:
        if self.stale_after is None or self.arrival_time is None:
            return False
        return now - self.arrival_time > self.stale_after

    def sample(self, now: float) -> str | None:
        if self.arrival_time is None or self.is_stale(now):
            return None
        if self.value is INVALID:
            return "?"
        return format_value(self.value)


def format_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)
