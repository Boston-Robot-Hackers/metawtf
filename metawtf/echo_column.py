#!/usr/bin/env python3
"""metawtf.echo_column: per-tick sampled state for an `echo` column.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from metawtf.field_extract import FieldPathError, extract_field

INVALID = object()  # message arrived but its field path could not be read


class EchoColumnState:
    def __init__(
        self,
        name: str,
        field: str,
        stale_after: float | None,
        width: int | None = None,
    ):
        self.name = name
        self.field = field
        self.stale_after = stale_after
        self.width = width
        self.value = None
        self.arrival_time = None

    def on_message(self, msg, now: float) -> None:
        # A bad path is usually a config typo, but crashing a live trace over it
        # is worse than flagging the cell; show "?" and keep the other columns.
        try:
            self.value = extract_field(msg, self.field)
        except FieldPathError:
            self.value = INVALID
        self.arrival_time = now

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
        return f"{value:.6g}"
    return str(value)
