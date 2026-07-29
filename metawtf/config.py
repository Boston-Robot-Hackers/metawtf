#!/usr/bin/env python3
"""metawtf.config: load and validate the metawtf.conf column configuration.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_SAMPLE_HZ = 5.0
DEFAULT_HZ_WINDOW = 2.0
# Minimum cell widths applied when a column omits `width`; values are sized for
# the metric's format (echo/hz print %.2f, proc_cpu/sys_cpu %.1f%%). Time keeps
# no default: the stamp's natural width varies with the chosen format.
DEFAULT_ECHO_WIDTH = 8
DEFAULT_HZ_WIDTH = 6
DEFAULT_PROC_CPU_WIDTH = 6
DEFAULT_SYS_CPU_WIDTH = 6
DIRECTIVES = {"sample", "time", "format", "echo", "hz", "proc_cpu", "sys_cpu"}
OUTPUT_FORMATS = {"human", "csv"}
COLUMN_METRICS = {"echo", "hz", "proc_cpu", "sys_cpu"}
TIME_KEYS = {"format", "width"}
ECHO_KEYS = {
    "name", "topic", "type", "field", "stale_after", "width",
    "json", "subfields",
}
ECHO_REQUIRED_KEYS = {"topic", "field"}
HZ_KEYS = {"topic", "match", "window", "name", "width"}
PROC_CPU_KEYS = {"name", "process", "width"}
SYS_CPU_KEYS = {"name", "mode", "width"}
SYS_CPU_MODES = {"busy", "idle"}


class ConfigError(Exception):
    """Raised when metawtf.conf fails validation."""


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
    subfield_widths: list[int] | None = None


@dataclass
class HzColumn:
    window: float
    topic: str | None = None
    match: re.Pattern | None = None
    name: str | None = None
    width: int | None = None


@dataclass
class ProcCpuColumn:
    name: str
    process: re.Pattern
    width: int | None = None


@dataclass
class SysCpuColumn:
    name: str
    mode: str
    width: int | None = None


@dataclass
class TimeColumn:
    format: str | None = None
    width: int | None = None


@dataclass
class Config:
    sample_hz: float
    columns: list[EchoColumn | HzColumn | ProcCpuColumn | SysCpuColumn]
    time: TimeColumn = field(default_factory=TimeColumn)
    # None means auto-detect from stdout (tty -> human, pipe -> csv).
    output_format: str | None = None


def sanitize_topic(topic: str) -> str:
    return topic.lstrip("/").replace("/", "_")


def parse_config(text: str) -> Config:
    sample_hz = DEFAULT_SAMPLE_HZ
    time_column = TimeColumn()
    output_format = None
    columns = []
    seen_singletons = set()
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            directive, positional, options = parse_line(line)
            if directive in COLUMN_METRICS:
                columns.append(parse_column(directive, positional, options))
            elif directive == "sample":
                sample_hz = parse_sample(positional, options, seen_singletons)
            elif directive == "format":
                output_format = parse_format(positional, options, seen_singletons)
            else:
                time_column = parse_time(positional, options, seen_singletons)
        except ConfigError as error:
            raise ConfigError(f"line {line_no}: {error}") from error
    if not columns:
        raise ConfigError("no column directives (echo/hz/proc_cpu/sys_cpu)")
    validate_windows(columns, sample_hz)
    return Config(
        sample_hz=sample_hz,
        columns=columns,
        time=time_column,
        output_format=output_format,
    )


def validate_windows(columns: list, sample_hz: float) -> None:
    # The sample directive may appear after hz lines, so the window-vs-period
    # rule is checked after the whole file is parsed.
    sample_period = 1.0 / sample_hz
    for column in columns:
        if isinstance(column, HzColumn) and column.window < sample_period:
            raise ConfigError(
                f"'window' {column.window:g} must be >= sample period"
                f" {sample_period:g}"
            )


def parse_line(line: str) -> tuple[str, str | None, dict]:
    tokens = line.split()
    directive, args = tokens[0], tokens[1:]
    if directive not in DIRECTIVES:
        raise ConfigError(
            f"unknown directive {directive!r};"
            f" expected one of {sorted(DIRECTIVES)}"
        )
    positional = None
    options = {}
    for token in args:
        if "=" not in token:
            if positional is not None:
                raise ConfigError(
                    f"at most one positional value, got {token!r} after"
                    f" {positional!r}"
                )
            positional = token
            continue
        key, _, value = token.partition("=")
        if not key or not value:
            raise ConfigError(f"malformed token {token!r}; expected key=value")
        if key in options:
            raise ConfigError(f"repeated key {key!r}")
        options[key] = value
    return directive, positional, options


def parse_sample(positional, options: dict, seen: set) -> float:
    reject_singleton_repeat("sample", seen)
    if options:
        raise ConfigError(f"'sample' takes no key=value options: {sorted(options)}")
    if positional is None:
        raise ConfigError("'sample' requires a value, e.g. 'sample 5'")
    return parse_float(positional, "sample_hz", must_be_positive=True)


def parse_time(positional, options: dict, seen: set) -> TimeColumn:
    reject_singleton_repeat("time", seen)
    if positional is not None:
        raise ConfigError(f"'time' takes no positional value, got {positional!r}")
    reject_unknown_keys(options, TIME_KEYS, "time")
    return TimeColumn(
        format=options.get("format"),
        width=parse_width(options.get("width")),
    )


def parse_format(positional, options: dict, seen: set) -> str:
    reject_singleton_repeat("format", seen)
    if options:
        raise ConfigError(f"'format' takes no key=value options: {sorted(options)}")
    if positional not in OUTPUT_FORMATS:
        raise ConfigError(
            f"'format' must be one of {sorted(OUTPUT_FORMATS)},"
            f" got {positional!r}"
        )
    return positional


def reject_singleton_repeat(directive: str, seen: set) -> None:
    if directive in seen:
        raise ConfigError(f"repeated '{directive}' directive")
    seen.add(directive)


def parse_column(
    directive: str, positional: str | None, options: dict
) -> EchoColumn | HzColumn | ProcCpuColumn | SysCpuColumn:
    if positional is not None:
        if directive not in ("echo", "hz"):
            raise ConfigError(
                f"'{directive}' takes no positional value, got {positional!r}"
            )
        if "topic" in options:
            raise ConfigError(
                f"topic given twice: positional {positional!r} and 'topic='"
            )
        options = {**options, "topic": positional}
    if directive == "echo":
        return parse_echo_column(options)
    if directive == "proc_cpu":
        return parse_proc_cpu_column(options)
    if directive == "sys_cpu":
        return parse_sys_cpu_column(options)
    return parse_hz_column(options)


def parse_echo_column(options: dict) -> EchoColumn:
    reject_unknown_keys(options, ECHO_KEYS, "echo")
    missing_keys = ECHO_REQUIRED_KEYS - set(options)
    if missing_keys:
        raise ConfigError(f"echo column missing key(s): {sorted(missing_keys)}")
    topic = options["topic"]
    field = options["field"]
    column_type = options.get("type")
    stale_after = parse_float_option(options, "stale_after")
    is_json = parse_bool(options.get("json", "false"), "json")
    subfields = parse_subfields(options.get("subfields"))
    name = resolve_echo_name(options, topic, is_json, subfields)
    width, subfield_widths = resolve_echo_widths(options, subfields)
    return EchoColumn(
        name=name,
        topic=topic,
        field=field,
        type=column_type,
        stale_after=stale_after,
        width=width,
        is_json=is_json,
        subfields=subfields,
        subfield_names=resolve_subfield_names(options, name, subfields),
        subfield_widths=subfield_widths,
    )


def resolve_echo_widths(
    options: dict, subfields: list[str] | None
) -> tuple[int | None, list[int] | None]:
    # Subfield columns render one cell each, so 'width' becomes a comma list
    # with one number per subfield; the single-column form keeps a lone width.
    if subfields is None:
        return parse_width(options.get("width"), DEFAULT_ECHO_WIDTH), None
    return None, parse_width_list(options.get("width"), len(subfields))


def resolve_echo_name(options, topic, is_json, subfields) -> str:
    if subfields is not None and not is_json:
        raise ConfigError("'subfields' requires 'json=true'")
    if subfields is not None and len(subfields) > 1 and "name" in options:
        raise ConfigError("'name' is not allowed with more than one subfield")
    return options.get("name") or sanitize_topic(topic)


def resolve_subfield_names(options, name, subfields) -> list[str] | None:
    if subfields is None:
        return None
    # An explicit name on a single-subfield selection is the column header
    # itself; otherwise headers are <base>_<key with dots as underscores>.
    if len(subfields) == 1 and "name" in options:
        return [name]
    return [subfield_name(name, key) for key in subfields]


def subfield_name(prefix: str, key: str) -> str:
    return f"{prefix}_{key.replace('.', '_')}"


def parse_hz_column(options: dict) -> HzColumn:
    reject_unknown_keys(options, HZ_KEYS, "hz")
    has_topic = "topic" in options
    has_match = "match" in options
    if has_topic == has_match:
        raise ConfigError("hz column requires exactly one of 'topic' or 'match'")
    window = parse_float(options.get("window", str(DEFAULT_HZ_WINDOW)), "window")
    width = parse_width(options.get("width"), DEFAULT_HZ_WIDTH)
    if has_match:
        if "name" in options:
            raise ConfigError("'name' is not allowed on an hz column with 'match'")
        pattern = compile_regex(options["match"], "match")
        return HzColumn(window=window, match=pattern, width=width)
    name = options.get("name") or sanitize_topic(options["topic"])
    return HzColumn(window=window, topic=options["topic"], name=name, width=width)


def parse_proc_cpu_column(options: dict) -> ProcCpuColumn:
    reject_unknown_keys(options, PROC_CPU_KEYS, "proc_cpu")
    name = require_key(options, "name")
    pattern = compile_regex(require_key(options, "process"), "process")
    width = parse_width(options.get("width"), DEFAULT_PROC_CPU_WIDTH)
    return ProcCpuColumn(name=name, process=pattern, width=width)


def parse_sys_cpu_column(options: dict) -> SysCpuColumn:
    reject_unknown_keys(options, SYS_CPU_KEYS, "sys_cpu")
    name = require_key(options, "name")
    mode = require_key(options, "mode")
    if mode not in SYS_CPU_MODES:
        raise ConfigError(
            f"'mode' must be one of {sorted(SYS_CPU_MODES)}, got {mode!r}"
        )
    width = parse_width(options.get("width"), DEFAULT_SYS_CPU_WIDTH)
    return SysCpuColumn(name=name, mode=mode, width=width)


def reject_unknown_keys(options: dict, valid_keys: set, where: str) -> None:
    unknown_keys = set(options) - valid_keys
    if unknown_keys:
        raise ConfigError(f"unknown key(s) in {where}: {sorted(unknown_keys)}")


def require_key(options: dict, key: str) -> str:
    if key not in options:
        raise ConfigError(f"missing required key {key!r}")
    return options[key]


def parse_float_option(options: dict, key: str) -> float | None:
    if key not in options:
        return None
    return parse_float(options[key], key, must_be_positive=True)


def parse_float(value: str, key: str, must_be_positive: bool = False) -> float:
    try:
        number = float(value)
    except ValueError:
        raise ConfigError(f"'{key}' must be a number, got {value!r}") from None
    if must_be_positive and number <= 0:
        raise ConfigError(f"'{key}' must be > 0, got {value!r}")
    return number


def parse_width(value: str | None, default: int | None = None) -> int | None:
    if value is None:
        return default
    return parse_positive_int(value, "width")


def parse_positive_int(value: str, key: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise ConfigError(f"'{key}' must be an integer, got {value!r}") from None
    if number <= 0:
        raise ConfigError(f"'{key}' must be > 0, got {value!r}")
    return number


def parse_width_list(value: str | None, count: int) -> list[int]:
    if value is None:
        return [DEFAULT_ECHO_WIDTH] * count
    parts = value.split(",")
    if len(parts) != count:
        raise ConfigError(
            f"'width' must have {count} comma-separated value(s) to match"
            f" 'subfields', got {len(parts)}"
        )
    return [parse_positive_int(part, "width") for part in parts]


def parse_bool(value: str, key: str) -> bool:
    if value not in ("true", "false"):
        raise ConfigError(f"'{key}' must be true or false, got {value!r}")
    return value == "true"


def parse_subfields(value: str | None) -> list[str] | None:
    if value is None:
        return None
    subfields = value.split(",")
    if any(not item for item in subfields):
        raise ConfigError(f"'subfields' must be non-empty keys, got {value!r}")
    return subfields


def compile_regex(pattern: str, key: str) -> re.Pattern:
    try:
        return re.compile(pattern)
    except re.error as err:
        raise ConfigError(f"invalid regex in '{key}' {pattern!r}: {err}") from err


def load_config(path) -> Config:
    try:
        text = Path(path).read_text()
    except OSError as error:
        raise ConfigError(f"cannot read config {path}: {error}") from error
    return parse_config(text)
