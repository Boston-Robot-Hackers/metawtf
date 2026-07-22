#!/usr/bin/env python3
"""metawtf.json_select: select a scalar from parsed JSON by a dotted key.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""


class JsonSelectError(Exception):
    """Raised when a dotted key is missing or does not resolve to a scalar."""


def select_json_value(data, key: str):
    value = data
    parts = key.split(".")
    for index, part in enumerate(parts):
        if not isinstance(value, dict) or part not in value:
            walked = ".".join(parts[:index]) or "<root>"
            raise JsonSelectError(f"{part!r} not found on {walked} (key {key!r})")
        value = value[part]
    # bool is a subclass of int, so it is accepted here as a scalar; None,
    # lists, and nested objects are not plottable and are rejected.
    if isinstance(value, (str, int, float)):
        return value
    raise JsonSelectError(f"key {key!r} did not resolve to a scalar: {value!r}")
