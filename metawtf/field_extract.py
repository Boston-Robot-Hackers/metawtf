#!/usr/bin/env python3
"""metawtf.field_extract: read a field path off a message object.

Author: Pito Salas and Claude Code
Open Source Under MIT license

A path is a dot-separated list of segments. A segment is a plain attribute
name, optionally followed by an integer index in brackets
(`detections[0]`, negative counts from the end). The final segment may
instead be a bare `#`, which resolves to `len(value)` instead of walking
further -- the one way to answer "how many" without a general expression
grammar.
"""

from dataclasses import dataclass


class FieldPathError(Exception):
    """Raised when a field path cannot be parsed or read off a message."""


@dataclass
class _Segment:
    name: str | None
    index: int | None = None
    is_length: bool = False


def parse_path(path: str) -> list[_Segment]:
    parts = path.split(".")
    last = len(parts) - 1
    segments = []
    for position, part in enumerate(parts):
        if part == "#":
            if position != last:
                raise FieldPathError(f"'#' must be the final segment (path {path!r})")
            segments.append(_Segment(name=None, is_length=True))
            continue
        if "#" in part:
            raise FieldPathError(f"'#' takes no index, got {part!r} (path {path!r})")
        segments.append(_parse_segment(part, path))
    return segments


def _parse_segment(part: str, path: str) -> _Segment:
    if "[" not in part:
        if "]" in part:
            raise FieldPathError(f"stray ']' in segment {part!r} (path {path!r})")
        return _Segment(name=part)
    name, _, rest = part.partition("[")
    if not rest.endswith("]") or "[" in rest[:-1]:
        raise FieldPathError(f"unclosed '[' in segment {part!r} (path {path!r})")
    index_text = rest[:-1]
    if not name:
        raise FieldPathError(
            f"index on an empty name in segment {part!r} (path {path!r})"
        )
    if not index_text:
        raise FieldPathError(f"empty index in segment {part!r} (path {path!r})")
    try:
        index = int(index_text)
    except ValueError as error:
        raise FieldPathError(
            f"non-integer index {index_text!r} in segment {part!r} (path {path!r})"
        ) from error
    return _Segment(name=name, index=index)


def extract_field(msg, path: str):
    value = msg
    walked_parts: list[str] = []
    for segment in parse_path(path):
        if segment.is_length:
            return _resolve_length(value, walked_parts, path)
        value = _resolve_attr(value, segment.name, walked_parts, path)
        walked_parts.append(segment.name)
        if segment.index is not None:
            value = _resolve_index(value, segment.index, walked_parts, path)
    return value


def _resolve_attr(value, name: str, walked_parts: list[str], path: str):
    if not hasattr(value, name):
        walked = ".".join(walked_parts) or "<root>"
        raise FieldPathError(f"{name!r} not found on {walked} (path {path!r})")
    return getattr(value, name)


def _resolve_index(value, index: int, walked_parts: list[str], path: str):
    walked = ".".join(walked_parts)
    try:
        return value[index]
    except TypeError as error:
        raise FieldPathError(f"{walked!r} is not indexable (path {path!r})") from error
    except IndexError as error:
        raise FieldPathError(
            f"index {index} out of range on {walked!r} (path {path!r})"
        ) from error


def _resolve_length(value, walked_parts: list[str], path: str):
    walked = ".".join(walked_parts) or "<root>"
    try:
        return len(value)
    except TypeError as error:
        raise FieldPathError(f"{walked!r} has no length (path {path!r})") from error
