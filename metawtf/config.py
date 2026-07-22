#!/usr/bin/env python3
"""metawtf.config: load and validate the metawtf.yaml column configuration.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re
from dataclasses import dataclass, field

DEFAULT_SAMPLE_HZ = 5.0
DEFAULT_HZ_WINDOW = 2.0
VALID_METRICS = {"echo", "hz"}
TOP_LEVEL_KEYS = {"sample_hz", "columns", "time"}
TIME_KEYS = {"format", "width"}
ECHO_KEYS = {
    "name", "metric", "topic", "type", "field", "stale_after", "width",
    "json", "subfields",
}
ECHO_REQUIRED_KEYS = {"metric", "topic", "field"}
HZ_KEYS = {"metric", "topic", "match", "window", "name", "width"}


class ConfigError(Exception):
    """Raised when metawtf.yaml fails validation."""


@dataclass
class EchoColumn:
    name: str
    topic: str
    field: str
    type: str | None = None
    stale_after: float | None = None
    width: int | None = None
    is_json: bool = False
    subfields: list[str] | None = None
    subfield_names: list[str] | None = None


@dataclass
class HzColumn:
    window: float
    topic: str | None = None
    match: re.Pattern | None = None
    name: str | None = None
    width: int | None = None


@dataclass
class TimeColumn:
    format: str | None = None
    width: int | None = None


@dataclass
class Config:
    sample_hz: float
    columns: list[EchoColumn | HzColumn]
    time: TimeColumn = field(default_factory=TimeColumn)


def sanitize_topic(topic: str) -> str:
    return topic.lstrip("/").replace("/", "_")


def parse_config(data: dict) -> Config:
    if not isinstance(data, dict):
        raise ConfigError("top-level config must be a mapping")
    unknown_keys = set(data) - TOP_LEVEL_KEYS
    if unknown_keys:
        raise ConfigError(f"unknown top-level key(s): {sorted(unknown_keys)}")
    sample_hz = parse_sample_hz(data.get("sample_hz", DEFAULT_SAMPLE_HZ))
    raw_columns = data.get("columns")
    if not isinstance(raw_columns, list) or not raw_columns:
        raise ConfigError("'columns' must be a non-empty list")
    sample_period = 1.0 / sample_hz
    columns = [parse_column(entry, sample_period) for entry in raw_columns]
    time = parse_time(data.get("time"))
    return Config(sample_hz=sample_hz, columns=columns, time=time)


def parse_time(data) -> TimeColumn:
    if data is None:
        return TimeColumn()
    if not isinstance(data, dict):
        raise ConfigError(f"'time' must be a mapping, got {data!r}")
    unknown_keys = set(data) - TIME_KEYS
    if unknown_keys:
        raise ConfigError(f"unknown key(s) in time: {sorted(unknown_keys)}")
    return TimeColumn(
        format=optional_str(data, "format"),
        width=parse_width(data.get("width")),
    )


def parse_sample_hz(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"sample_hz must be a number, got {value!r}")
    if value <= 0:
        raise ConfigError(f"sample_hz must be > 0, got {value!r}")
    return float(value)


def parse_column(entry: dict, sample_period: float) -> EchoColumn | HzColumn:
    if not isinstance(entry, dict):
        raise ConfigError(f"column entry must be a mapping, got {entry!r}")
    metric = entry.get("metric")
    if metric not in VALID_METRICS:
        raise ConfigError(
            f"unknown metric {metric!r}; expected one of {sorted(VALID_METRICS)}"
        )
    if metric == "echo":
        return parse_echo_column(entry)
    return parse_hz_column(entry, sample_period)


def parse_echo_column(entry: dict) -> EchoColumn:
    unknown_keys = set(entry) - ECHO_KEYS
    if unknown_keys:
        raise ConfigError(f"unknown key(s) in echo column: {sorted(unknown_keys)}")
    missing_keys = ECHO_REQUIRED_KEYS - set(entry)
    if missing_keys:
        raise ConfigError(f"echo column missing key(s): {sorted(missing_keys)}")
    topic = require_str(entry, "topic")
    field = require_str(entry, "field")
    column_type = optional_str(entry, "type")
    stale_after = parse_stale_after(entry.get("stale_after"))
    is_json = parse_bool(entry.get("json", False), "json")
    subfields = parse_subfields(entry.get("subfields"))
    name = resolve_echo_name(entry, topic, is_json, subfields)
    return EchoColumn(
        name=name,
        topic=topic,
        field=field,
        type=column_type,
        stale_after=stale_after,
        width=parse_width(entry.get("width")),
        is_json=is_json,
        subfields=subfields,
        subfield_names=resolve_subfield_names(entry, name, subfields),
    )


def resolve_echo_name(entry, topic, is_json, subfields) -> str:
    if subfields is not None and not is_json:
        raise ConfigError("'subfields' requires 'json: true'")
    if subfields is not None and len(subfields) > 1 and "name" in entry:
        raise ConfigError("'name' is not allowed with more than one subfield")
    name = entry.get("name") or sanitize_topic(topic)
    if not isinstance(name, str):
        raise ConfigError(f"'name' must be a string, got {name!r}")
    return name


def resolve_subfield_names(entry, name, subfields) -> list[str] | None:
    if subfields is None:
        return None
    # An explicit name on a single-subfield selection is the column header
    # itself; otherwise headers are <base>_<key with dots as underscores>.
    if len(subfields) == 1 and "name" in entry:
        return [name]
    return [subfield_name(name, key) for key in subfields]


def subfield_name(prefix: str, key: str) -> str:
    return f"{prefix}_{key.replace('.', '_')}"


def parse_bool(value, key: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"'{key}' must be true or false, got {value!r}")
    return value


def parse_subfields(value) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        raise ConfigError(f"'subfields' must be a non-empty list, got {value!r}")
    for item in value:
        if not isinstance(item, str) or not item:
            raise ConfigError(
                f"each subfield must be a non-empty string, got {item!r}"
            )
    return value


def parse_hz_column(entry: dict, sample_period: float) -> HzColumn:
    unknown_keys = set(entry) - HZ_KEYS
    if unknown_keys:
        raise ConfigError(f"unknown key(s) in hz column: {sorted(unknown_keys)}")
    has_topic = "topic" in entry
    has_match = "match" in entry
    if has_topic == has_match:
        raise ConfigError("hz column requires exactly one of 'topic' or 'match'")
    window = parse_window(entry.get("window", DEFAULT_HZ_WINDOW), sample_period)
    width = parse_width(entry.get("width"))
    if has_match:
        if "name" in entry:
            raise ConfigError("'name' is not allowed on an hz column with 'match'")
        pattern = compile_regex(require_str(entry, "match"))
        return HzColumn(window=window, match=pattern, width=width)
    topic = require_str(entry, "topic")
    name = entry.get("name") or sanitize_topic(topic)
    if not isinstance(name, str):
        raise ConfigError(f"'name' must be a string, got {name!r}")
    return HzColumn(window=window, topic=topic, name=name, width=width)


def parse_window(value, sample_period: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"window must be a number, got {value!r}")
    if value < sample_period:
        raise ConfigError(
            f"window {value!r} must be >= sample period {sample_period:g}"
        )
    return float(value)


def parse_width(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"width must be an integer, got {value!r}")
    if value <= 0:
        raise ConfigError(f"width must be > 0, got {value!r}")
    return value


def compile_regex(pattern: str) -> re.Pattern:
    try:
        return re.compile(pattern)
    except re.error as err:
        raise ConfigError(f"invalid regex {pattern!r}: {err}") from err


def require_str(entry: dict, key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"'{key}' must be a non-empty string, got {value!r}")
    return value


def optional_str(entry: dict, key: str) -> str | None:
    if key not in entry:
        return None
    return require_str(entry, key)


def parse_stale_after(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"stale_after must be a number, got {value!r}")
    if value <= 0:
        raise ConfigError(f"stale_after must be > 0, got {value!r}")
    return float(value)


def load_config(path) -> Config:
    import yaml

    with open(path) as config_file:
        data = yaml.safe_load(config_file)
    return parse_config(data or {})
