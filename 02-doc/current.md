# Current Status — Session Handoff

**Last updated:** 2026-07-24

## State
Developing on ROS2 Jazzy (real `rclpy`/`rosidl` available). Full suite:
**191 passed** via `python3 -m pytest test/`.

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
