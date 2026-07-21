#!/usr/bin/env python3
"""metawtf.config: load and validate the metawtf.yaml column configuration.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from dataclasses import dataclass

DEFAULT_SAMPLE_HZ = 5.0
VALID_METRICS = {"echo"}
TOP_LEVEL_KEYS = {"sample_hz", "columns"}
ECHO_KEYS = {"name", "metric", "topic", "type", "field", "stale_after"}
ECHO_REQUIRED_KEYS = {"metric", "topic", "field"}


class ConfigError(Exception):
    """Raised when metawtf.yaml fails validation."""


@dataclass
class EchoColumn:
    name: str
    topic: str
    field: str
    type: str | None = None
    stale_after: float | None = None


@dataclass
class Config:
    sample_hz: float
    columns: list[EchoColumn]


def sanitize_topic(topic: str) -> str:
    return topic.lstrip("/").replace("/", "_")


def default_column_name(topic: str, field: str) -> str:
    last_segment = field.split(".")[-1]
    return f"{sanitize_topic(topic)}_{last_segment}"


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
    columns = [parse_column(entry) for entry in raw_columns]
    return Config(sample_hz=sample_hz, columns=columns)


def parse_sample_hz(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"sample_hz must be a number, got {value!r}")
    if value <= 0:
        raise ConfigError(f"sample_hz must be > 0, got {value!r}")
    return float(value)


def parse_column(entry: dict) -> EchoColumn:
    if not isinstance(entry, dict):
        raise ConfigError(f"column entry must be a mapping, got {entry!r}")
    metric = entry.get("metric")
    if metric not in VALID_METRICS:
        raise ConfigError(f"unknown metric {metric!r}; only 'echo' is supported")
    return parse_echo_column(entry)


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
    name = entry.get("name") or default_column_name(topic, field)
    if not isinstance(name, str):
        raise ConfigError(f"'name' must be a string, got {name!r}")
    return EchoColumn(
        name=name,
        topic=topic,
        field=field,
        type=column_type,
        stale_after=stale_after,
    )


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
