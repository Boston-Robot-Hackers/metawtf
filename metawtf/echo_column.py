#!/usr/bin/env python3
"""metawtf.echo_column: per-tick sampled state for an `echo` column.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from metawtf.field_extract import FieldPathError, extract_field
from metawtf.value_column import INVALID, ValueColumnState


class EchoColumnState(ValueColumnState):
    kind = "echo"

    def __init__(
        self,
        name: str,
        field: str,
        stale_after: float | None,
        width: int | None = None,
    ):
        super().__init__(name, stale_after, width)
        self.field = field

    def on_message(self, msg, now: float) -> None:
        # A bad path is usually a config typo, but crashing a live trace over it
        # is worse than flagging the cell; show "?" and keep the other columns.
        try:
            self.value = extract_field(msg, self.field)
        except FieldPathError:
            self.value = INVALID
        self.arrival_time = now
