# TF13 Buddy's display requests for Feature F13

**Date Created:** 2026-09-07

## TF13.0 — keep pinned header pinned across vertical resize

**Status**: done
**Description**: Implemented as poll-based size-change detection each
`sample_hz` tick (`Sampler.tick` in `sampler.py`), not a `SIGWINCH` handler —
simpler, portable (no signal on Windows), and consistent with the codebase's
existing poll-driven header-growth check. `Sampler` gained a `get_size`
callable; `tick()` now re-emits the header whenever the column count *or*
the terminal size differs from the last emission, which drives
`terminal.py`'s already-tested fresh-size scroll-region recalculation (see
`test_draw_header_reissues_region_from_a_fresh_size`). Test:
`test_header_reprinted_on_terminal_resize_with_no_column_change` and
`test_header_not_reprinted_when_size_is_unchanged` in `test_sampler.py`.

## TF13.1 — parse `width=N%` alongside `width=N`

**Status**: done
**Description**: `config.py` gained a `PercentWidth` dataclass;
`parse_width()`/`parse_width_list()` route a trailing `%` through a new
`parse_percent_width()`, coexisting with plain `width=N` on other columns
in the same config (including mixed within one comma list). Test:
`test_percent_width_parses_on_echo_and_hz_columns`,
`test_percent_width_over_100_raises`, `test_percent_width_zero_raises`,
`test_non_numeric_percent_width_raises`,
`test_percent_width_in_multi_field_list`,
`test_time_percent_width_parses` in `test_config.py`.

## TF13.2 — resolve percentage widths at render time

**Status**: done
**Description**: `sampler.py` gained `resolve_width()`, called from
`format_header()`, `format_row()`, and `join_group_header()` against
`Sampler.terminal_columns()` (which queries `get_size()` only in human mode,
since csv ignores width). Rows re-resolve every tick naturally; the header
re-resolves via TF13.0's size-change detection. Test:
`test_resolve_width_passes_through_plain_int_and_none`,
`test_resolve_width_computes_percent_of_terminal_columns`,
`test_resolve_width_clamps_percent_to_at_least_one`,
`test_percent_width_column_scales_with_terminal_width`,
`test_percent_width_column_re_resolves_after_resize`,
`test_csv_mode_ignores_resize_and_never_queries_terminal_size` in
`test_sampler.py`.

## TF13.3 — document the `proc_cpu`/`sys_cpu` same-machine requirement

**Status**: done
**Description**: Added an explicit paragraph to `README.md`'s
`proc_cpu`/`sys_cpu` section stating both read from local `/proc`, so
`metawtf` must run on the same machine as the ROS2 node(s) being measured.
Also documented `width=N%` in the same pass (config reference tables plus a
new "Percentage widths" subsection under "Human format"). `02-doc/spec.md`
does not document these metrics at all, so no change was needed there. No
test — docs only.

## TF13.4 — test-writing task

**Status**: done
**Description**: Coverage added directly alongside TF13.0–TF13.2 above
(14 new tests across `test_config.py`/`test_sampler.py`), covering the
edge cases identified up front: a percentage resolving below a viable
minimum (clamped to 1), 0%/>100% rejection at parse time, mixed
fixed/percent widths in one comma list, and csv mode never querying
terminal size at all. Full suite: 244 passed, 4 skipped, and the same 10
pre-existing `rosidl_runtime_py`-only failures noted in `02-doc/current.md`
(no ROS2 install on this machine) — unrelated to this feature.
