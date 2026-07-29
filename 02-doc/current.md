# Current Status — Session Handoff

**Last updated:** 2026-07-29

## State
Developing on ROS2 Jazzy (real `rclpy`/`rosidl` available). Full suite:
**223 passed** via `uv run pytest` (base `python3` lacks numpy; use `uv run`).

**Per-subfield width (chore): DONE** — for a `json` echo column with explicit
`subfields`, `width=` is now a comma list with one number per subfield
(`subfields=a,b,c width=4,10,6`); count must match or `ConfigError`. Omitted →
each defaults to `DEFAULT_ECHO_WIDTH` (8). `EchoColumn.subfield_widths`
(list[int]|None) carries them; `resolve_echo_widths`/`parse_width_list` in
`config.py`; `column_manager.add_echo_column` zips a width per state. Non-json
and single-column echo widths unchanged (single int). Tests in
`test/test_config.py`. Literate 02-config regen pending. Uncommitted.

**F08 (header tail-truncation): DONE and closed** — a column header wider than
its width is now cut to the width keeping its **tail** (`…` at front, e.g.
`cpu_nav2`→`…_nav2`); columns no longer widen to fit the name. `effective_width`
removed from `sampler.py`; `truncate_tail` added; data cells still keep their
head. README + literate 18-sampler updated. Uncommitted.

**F09 (clear screen on start): DONE and closed** — `PinnedHeader.setup` emits
`CSI 2J` before drawing so the first pinned header lands on a clean screen (was
easy to miss amid prior terminal content). Pinned/tty path only; csv/redirect
untouched. Literate X02-terminal updated. Uncommitted.

**F07 (output formats + pinned header): DONE and closed** — `format human|csv`
directive (`Config.output_format`, None = auto-detect); `Sampler` takes
keyword-only `human=` plus an `on_header` hook and renders either padded,
`…`-truncated human rows or pure RFC-4180 csv; new `metawtf/terminal.py`
`PinnedHeader` freezes the header via an ANSI scroll region (DECSTBM) with
clean restore on quit; `tracer_node` resolves the mode (`format` wins, else
`sys.stdout.isatty()`) and wires `pinned.show` as `on_header`. csv mode
verified end-to-end against a live `ros2 topic pub`; pinned header on a real
terminal verified by the user 2026-07-25. Docs: spec, README,
`metawtf.conf` grammar, literate regen (01, 18, 20, new X02-terminal,
00-overview bumped). Gotcha: xterm-style terminals do not add rows scrolled
off a scroll region to scrollback — redirect csv for a full record.

**F05 (conf-only config): DONE and closed** — YAML is gone. `config.py`
parses line-oriented `metawtf.conf` (directive + positional + `key=value`,
string coercion in the validators, line-numbered errors); default config is
`./metawtf.conf`; pyyaml dropped from `package.xml`; `~/ros2_ws/metawtf.conf`
is the live config (yaml deleted); repo sample is `metawtf/metawtf.conf` with
a formal grammar header; README/spec rewritten; F05/TF05 moved to `done/`.

**F06 (sys_cpu): DONE and closed** — system-wide busy/idle CPU from
`/proc/stat` (`mode=busy|idle`, `%.1f%%`); feature/task files created
retroactively and filed in `done/`. Also landed: proc_cpu prints with `%`,
per-metric default widths (echo 8, others 6), columns auto-widen to fit
headers, every comma followed by a space in output.

**Literate docs fully regenerated** per the new `.claude/literate.md` (copied
from dome_nav — adds algorithm/theory depth and architecture overviews):
all 21 modules covered, renumbered in dependency order, plus a new
`01-literate/00-overview.md` (theory of operation).

**F03 (TF03): code done, T06 open** — T01–T05 marked done (implemented and
tested); the live busyloop demo + colcon check remain. F03 file amended:
system-wide CPU removed from non-goals (became F06), example in conf syntax,
`%.1f%%` format.

**F01 (TF01): DONE and closed** — echo columns, moved to `done/`.

**F02 (TF02): DONE and closed** — hz columns by `topic` or `match` regex.
Live tf demo verified by the user 2026-07-22; moved to `done/`.

**F04 (TF04): DONE and closed** — JSON-string fields expanded into subfield
columns; live demo verified by the user 2026-07-22; moved to `done/`.

## Chores landed this session (`04-tasks/chores.md`)
- Floats print with 2 decimals everywhere (echo `.2f`, hz `.2f`).
- Padded cells put the comma right after the value (`join_cells` in sampler):
  `1.50,      ` not `1.50      ,`.
- `h` keypress and `-h` flag print the same help; `-f <yaml>` overrides the
  config path. Hand-rolled `parse_cli`, no argparse.

## Gotcha resolved this session
The installed build in `~/ros2_ws/install` was stale (pre-F04) and shadowed the
source, making the JSON columns "not work." After any source change:
`colcon build --packages-select metawtf && source install/setup.bash`.

## Open chore
- `colcon test` collects 0 tests though plain `pytest` finds 112; add pytest
  discovery config so the colcon path is green too.

## Parked
- Standalone (non-ROS) install / packaging beyond the `setup.cfg` bin trick —
  revisit only if needed. (The old "F04 CLI" idea; the F04 number was reused
  for json subfields.)

## Open Questions
- None.
