# TF07 Tasks for Feature F07 — Human/CSV output formats with pinned header

## T01 — `format` directive parsing
**Status**: done
**Description**: Add `format` to `DIRECTIVES` in `metawtf/config.py`; parse it
as a singleton with one positional value (`human` or `csv`), no `key=value`
options, repeat is an error. `Config` gains `output_format: str | None = None`.
Tests in `test/test_config.py`: both valid values; bad value, options,
repeat, and missing positional each rejected with a line-numbered error.

## T02 — Sampler csv/human render modes
**Status**: done
**Description**: `metawtf/sampler.py` `Sampler` gains a `human: bool`. csv
mode joins with bare commas + `quote_cell`, no padding, no truncation. human
mode keeps the padded join, drops quoting, and truncates values (not headers)
to `effective_width` with `…`. Header reprint on column growth stays in both
modes. Tests in `test/test_sampler.py`: csv exact strings incl. quoting of
comma/quote values; human `…` truncation; short-value alignment unchanged;
header reprint on growth both modes.

## T03 — `terminal.py` PinnedHeader
**Status**: done
**Description**: New module `metawtf/terminal.py`, class `PinnedHeader`:
ANSI scroll-region (DECSTBM) boundary with injectable `get_size` (default
`shutil.get_terminal_size`) and `out`. `setup(header_lines)` prints the header
at home, issues the region below it, parks the cursor on the last row;
`draw_header(lines)` redraws in place and re-issues the region (column growth,
resize); `close()` resets the region and drops the cursor below the output,
idempotent. Tests in `test/test_terminal.py` with `StringIO` and a fake size:
escape sequences, region math, redraw sequence, idempotent close.

## T04 — tracer_node wiring and clean shutdown
**Status**: done
**Description**: `metawtf/tracer_node.py` resolves the mode
(`config.output_format` or tty auto-detect), builds `Sampler(human=...)`,
creates `PinnedHeader` only in human mode on a tty, routes header prints
through it, and closes it in the existing shutdown `finally` (q / Ctrl-C /
stdin EOF). ROS boundary: no new unit tests here; the pieces are covered by
T01–T03 and the live demo is manual.

## T05 — Docs and housekeeping
**Status**: done
**Description**: Add the `format` directive to the grammar header of
`metawtf/metawtf.conf`; amend `02-doc/spec.md` Overview (two formats,
auto-detect, pinned header); update `README.md`'s output section; regenerate
literate docs per `.claude/literate.md` for `config`, `sampler`,
`tracer_node`, and new `terminal`; update `02-doc/current.md`. Not unit
testable — verified by review.

## T06 — Full suite, live demo, close feature
**Status**: done
**Description**: `python3 -m pytest test/` green (217 passed). csv mode verified
end-to-end against a live `ros2 topic pub` publisher; the pinned-header escape
sequence lifecycle is covered by `test_terminal.py` (pty eyeball on a real
terminal left to the user). F07/TF07 statuses flipped; both moved to `done/`.
