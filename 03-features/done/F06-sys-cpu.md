# F06 — System-wide CPU columns (sys_cpu)

**Priority**: Medium
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes

**Description**: Add `sys_cpu` columns reporting overall machine CPU from the
aggregate line of `/proc/stat`. `mode=busy` or `mode=idle` selects which
percent the column renders; busy = user+nice+system+irq+softirq+steal, idle =
idle+iowait (top convention), guest fields not double-counted. Percent is
Δpart/Δtotal × 100 — a pure ratio, so no wall clock or clk_tck is needed and
busy+idle sums to 100 across the whole machine (Solaris mode, unlike
proc_cpu's per-core scale). Formatted `%.1f%%`; first sample and unreadable
stat produce an empty cell. (Feature file created retroactively — the code
landed alongside F03 before the file existed.)

```
sys_cpu name=cpu_busy mode=busy
sys_cpu name=cpu_idle mode=idle
```

## How to Demo
**Setup**: Package built and sourced; conf with `sys_cpu` columns.

**Steps**:
1. `metawtf`
2. Start a busy process, watch `cpu_busy` rise and `cpu_idle` fall.

**Expected output**: busy + idle ≈ 100 at every tick; `%.1f%%` formatting;
empty cells only on the first tick.

## Non-Goals (this feature)
- Per-core breakdown, per-thread metrics, non-Linux platforms.
