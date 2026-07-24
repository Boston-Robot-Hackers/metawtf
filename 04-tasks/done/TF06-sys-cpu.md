# TF06 — System-wide CPU columns, tasks for Feature F06

Retroactive task file: the work landed in one session alongside F03; all
tests run without ROS via an injectable stat reader.

## T01 — Aggregate /proc/stat parser
**Status**: done
**Description**: `metawtf/sys_stat.py` — first-line `cpu` parse to
(busy, idle) jiffies; short lines zero-padded; malformed lines raise;
unreadable file returns None.
**Test**: `test/test_sys_stat.py` — field classification, guest
double-count guard, missing fields, malformed input, tmpdir file read.

## T02 — System CPU tracker
**Status**: done
**Description**: `metawtf/sys_cpu_tracker.py` — baseline/delta ratio
Δpart/Δtotal × 100; first sample None; unreadable stat resets baseline;
zero total delta → None.
**Test**: `test/test_sys_cpu_tracker.py` — scripted reader sequence,
percents sum to 100, baseline reset.

## T03 — sys_cpu column + config + wiring
**Status**: done
**Description**: `metawtf/sys_cpu_column.py` (mode selects busy/idle,
`%.1f%%`); `sys_cpu` schema in `config.py` with mode validation and default
width 6; `ColumnManager` branch with no subscription.
**Test**: `test/test_sys_cpu_column.py`, sys_cpu cases in
`test/test_config.py` and `test/test_column_manager.py`.
