#!/usr/bin/env python3
"""metawtf.json_column: sampled state for one key of a JSON-string field.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import json

from metawtf.field_extract import FieldPathError, extract_field
from metawtf.json_select import JsonSelectError, select_json_value
from metawtf.value_column import INVALID, ValueColumnState


class JsonEchoColumnState(ValueColumnState):
    """Extracts a string field, parses it as JSON, and selects one scalar key.

    Every failure mode along the way — the field path is bad, the string is not
    valid JSON, the key is missing, or the key is not a scalar — collapses to the
    `INVALID` sentinel so the cell shows "?" rather than crashing the trace.
    """

    def __init__(
        self,
        name: str,
        field: str,
        key: str,
        stale_after: float | None,
        width: int | None = None,
    ):
        super().__init__(name, stale_after, width)
        self.field = field
        self.key = key

    def on_message(self, msg, now: float) -> None:
        try:
            raw = extract_field(msg, self.field)
            self.value = select_json_value(json.loads(raw), self.key)
        except (FieldPathError, JsonSelectError, ValueError, TypeError):
            self.value = INVALID
        self.arrival_time = now
