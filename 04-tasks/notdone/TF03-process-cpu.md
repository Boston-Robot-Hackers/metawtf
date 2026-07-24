# TF03 — Process CPU columns, tasks for Feature F03

Depends on F01 (config loader, sampler, node scaffold). All tests run without
live processes or a ROS graph: the /proc root, clock, and stat reader are
injectable.

## T01 — Schema: proc_cpu entries
**Status**: done
**Description**: Extend the column schema: `metric: proc_cpu` requires `name`
and `process` (regex matched against cmdline, compiled at load; invalid regex
→ clear error).
**Test**: Unit test — valid entry parses; missing `name`, missing `process`,
bad regex → clear errors.

## T02 — /proc/<pid>/stat parser
**Status**: done
**Description**: Pure function from stat-line string to total jiffies
(utime + stime, fields 14 and 15). Split after the LAST `)` so comm values
with spaces or parens parse correctly.
**Test**: Unit test — synthetic stat lines, including comm containing spaces
and parentheses, yield the expected jiffies sum.

## T03 — Process resolver
**Status**: done
**Description**: Scan an injectable proc root (default `/proc`): for each
numeric pid directory read `cmdline` (NULs → spaces), keep pids matching the
regex; skip our own pid; unreadable/empty cmdline → skip. Returns a pid set.
**Test**: Unit test against a tmpdir fake proc tree — matching python-style
cmdline, non-matching entry, empty cmdline, own-pid exclusion.

## T04 — CPU tracker
**Status**: done
**Description**: State `{pid: (jiffies, wall_t)}`. On `sample(now)`: resolve
pids, read jiffies per pid; where a previous baseline exists accumulate
(Δjiffies / clk_tck) / Δwall × 100; store the new baseline; drop vanished pids.
Return the summed percent, or None when no pid had a baseline (first sighting,
or no matching process). clk_tck via `os.sysconf('SC_CLK_TCK')`, injectable.
**Test**: Unit test with fake stat reader + fake clock — known deltas produce
the expected percent (including > 100 for two "cores" of work); first sample
None; vanished pid excluded; two pids summed.

## T05 — proc_cpu column integration
**Status**: done
**Description**: Column `sample()` returns the percent formatted `%.1f%%`
(e.g. `100.0%`), or None (empty cell) when the process is absent or newly
seen. Wired into the sampler like other metrics.
**Test**: Unit test — exact row output with a cpu value, and empty cell when
the process is absent.

## T06 — Feature test suite + demo verification
**Status**: not done
**Description**: T01–T05 pass together; demo:
`bash -c 'exec -a busyloop python3 -c "while True: pass"' &`, config matching
`busyloop`, then kill the process.
**Test**: `colcon test --packages-select metawtf` green; demo shows ~100 in the
cpu column while the loop runs and an empty cell after the kill.
