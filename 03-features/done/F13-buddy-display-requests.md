# F13 — Buddy's display requests: resize-safe header, % column widths, CPU-column doc

**Priority**: Medium
**Date Created:** 2026-09-07
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes

**Description**: Three related requests from Buddy about the live terminal
display and its config:

1. **Pinned header survives vertical resize.** The header is pinned via an
   ANSI scroll region (`terminal.py`) recalculated from
   `shutil.get_terminal_size()`, but today that recalculation only happens
   when a *new column* triggers a header redraw. A plain vertical resize of
   the terminal window (no column change) is never detected, so the header
   scrolls away with the data. Fix: detect terminal-size changes (e.g. a
   `SIGWINCH` handler) and re-pin/redraw the header whenever the size
   changes, not only on column-set changes.

2. **Percentage-based column widths.** `width=N` (fixed character count) is
   the only width syntax today. Add `width=N%` as an alternative that
   coexists with the existing fixed syntax — a column can specify either
   form. A percentage width resolves against the current terminal width at
   render time, so it adapts automatically if the user resizes the terminal
   horizontally.

3. **Document the same-machine requirement for `proc_cpu`/`sys_cpu`.**
   Both metrics read from the local `/proc` filesystem
   (`/proc/<pid>/stat`, `/proc/stat`), so they only report meaningful data
   when `metawtf` runs on the same machine as the ROS2 node(s) being
   measured. This is implicit in the code and literate docs but never
   stated in `README.md` or `02-doc/spec.md`. Add an explicit line.

## How to Demo

**Setup**: `metawtf` running against a config with at least one `echo` or
`hz` column, in an interactive terminal.

**Steps**:
1. Start `metawtf`; resize the terminal window vertically (shrink then
   grow) without adding/removing any topic activity. Confirm the header
   stays pinned at the top and only data rows scroll beneath it.
2. Add a column with `width=20%` to the config; resize the terminal
   horizontally and confirm the column's rendered width tracks the
   percentage of current terminal width, coexisting with other columns
   still using fixed `width=N`.
3. Check `README.md`'s `proc_cpu`/`sys_cpu` section (and `02-doc/spec.md`
   if it documents these metrics) for the same-machine note.

**Expected output**: header never scrolls off on vertical resize;
percentage-width columns resize live with the terminal; docs state the
`proc_cpu`/`sys_cpu` locality requirement.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code or content until the
user gives explicit approval to proceed.
