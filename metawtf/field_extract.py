#!/usr/bin/env python3
"""metawtf.field_extract: read a dotted attribute path off a message object.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""


class FieldPathError(Exception):
    """Raised when a dotted field path cannot be read off a message."""


def extract_field(msg, path: str):
    value = msg
    parts = path.split(".")
    for index, part in enumerate(parts):
        if not hasattr(value, part):
            walked = ".".join(parts[:index]) or "<root>"
            raise FieldPathError(f"{part!r} not found on {walked} (path {path!r})")
        value = getattr(value, part)
    return value
