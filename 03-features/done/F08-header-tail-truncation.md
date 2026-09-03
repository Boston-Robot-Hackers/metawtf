# F08 — Truncate long column headers to their tail
**Priority**: Low
**Date Created:** 2026-07-25
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: When a column's name is longer than the column's available
width, show as much of the *end* of the name as fits, prefixed with `…`,
instead of widening the column to fit the whole name. This keeps rows and the
header aligned at the configured width. Data cells still truncate from the
*front* (keep the head, `…` at the end); only headers keep the tail. Applies to
human (padded) mode only; csv mode is untouched (no padding, never truncated).

Replaces the current `effective_width` behaviour, which widened a column to the
header length so headers were never cut.

## How to Demo
**Setup**: A `metawtf.conf` with a column whose name is longer than its width
(e.g. an hz `match` column named `cpu_nav2` in a width-6 column).

**Steps**:
1. Run metawtf against a live topic in a terminal (human mode).
2. Observe a long header name.

**Expected output**: The header cell shows `…` plus the trailing characters of
the name, fitting exactly in the column width; the header stays aligned with the
data rows below it.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
