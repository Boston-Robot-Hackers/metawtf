# TF05 — Conf-only config format, tasks for Feature F05

Depends on F01 (config loader) and F03 (proc_cpu columns; sys_cpu landed in
the same schema). All tests run without ROS: the parser is pure text in,
dataclasses out.

## T01 (done) — Lexer: lines to (directive, positional, options)
**Status**: done
**Description**: `parse_config(text)` skips blanks/`#` lines, splits tokens,
separates the single positional from `key=value` options. Errors with line
numbers: unknown directive, two positionals, bare token after the positional,
malformed or repeated `key=value`.
**Test**: Unit tests per error case plus comment/blank handling; error
messages contain the line number.

## T02 (done) — Directives and string-based validators
**Status**: done
**Description**: `sample`, `time`, `echo`, `hz`, `proc_cpu`, `sys_cpu`
directives build the existing dataclasses. Validators take strings and coerce:
`width` int, `window`/`stale_after`/`sample_hz` float, `json` true/false,
`subfields` comma-split. All prior schema rules unchanged (required/unknown
keys, name-with-match, mode set, regex compile, default widths).
**Test**: Port every `test_config.py` case to conf lines; add coercion-failure
cases (bad int, bad float, bad bool).

## T03 (done) — load_config, CLI, and packaging
**Status**: done
**Description**: `load_config` reads text (no yaml import); `CONFIG_FILENAME`
becomes `metawtf.conf`; help text updated; `python3-yaml` dropped from
`package.xml`.
**Test**: Update `test_tracer_node.py` path/help expectations; missing-file
error test stays green.

## T04 (done) — Convert configs and docs
**Status**: done
**Description**: `~/ros2_ws/metawtf.yaml` → `metawtf.conf` (yaml deleted);
repo sample `metawtf/metawtf.yaml` → `metawtf/metawtf.conf`; README config
section and `02-doc/spec.md` rewritten for conf.
**Test**: `load_config` on the real `~/ros2_ws/metawtf.conf` parses (manual);
README example matches the parser (unit test optional).

## T05 (done) — Feature test suite
**Status**: done
**Description**: Full `python3 -m pytest test/` green; literate docs for
`config.py` and `tracer_node.py` regenerated before commit.
**Test**: `python3 -m pytest test/` all pass.
