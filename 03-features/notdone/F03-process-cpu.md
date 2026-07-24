# F03 — Process CPU columns

**Priority**: Medium
**Done:** no
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes

**Description**: Add `proc_cpu` columns to the sampled table, reporting CPU% of
a process selected by regex against its command line. Sampled per tick from
`/proc/<pid>/stat` — standard library only, no psutil dependency. Motivating
case: "percent CPU of the `controller_server` process, on the same rows as
topic data." (System-wide busy/idle CPU landed alongside as `sys_cpu`.)

```
proc_cpu name=cpu_nav2 process=controller_server
```

Correctness rules:
- cpu% = (Δ(utime+stime) / clk_tck) / Δwall × 100 — the same formula psutil
  uses. clk_tck from `os.sysconf('SC_CLK_TCK')`. 100% = one fully used core;
  multi-threaded processes can exceed 100% (same convention as top's Irix
  mode).
- The stat line is parsed after the **last** `)` — comm may contain spaces or
  parens. utime and stime are fields 14 and 15.
- Match against the full cmdline (NUL-separated args joined with spaces),
  **not** comm: Python ROS nodes all have comm `python3`.
- Multiple matching pids: their CPU% is summed. Pids are re-resolved every
  tick (a `/proc` scan is cheap at trace rates) so restarts are picked up;
  vanished pids are dropped from the baseline.
- The first tick after a pid appears has no baseline → empty cell. (psutil's
  `cpu_percent()` famously returns a meaningless 0.0 on first call; we show
  nothing instead.) Process not running → empty cell.
- metawtf's own pid is excluded from matches.

## How to Demo
**Setup**: Package built and sourced; config with a `proc_cpu` column matching
a test process.

**Steps**:
1. Start a busy process: `bash -c 'exec -a busyloop python3 -c "while True: pass"' &`
2. `ros2 run metawtf metawtf`
3. Kill the busy process.

**Expected output**: The cpu column reads ~100 while the loop runs (one full
core) and goes empty after the kill.

## Non-Goals (this feature)
- Memory, IO, network, per-thread metrics.
- Normalizing by core count (raw psutil/top-style percent only).
- Non-Linux platforms.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code until the user approves.
