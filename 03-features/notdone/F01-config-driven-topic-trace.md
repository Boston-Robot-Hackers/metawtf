# F01 — Config-driven sampled table trace

**Priority**: High
**Done:** no
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** partial — 25/29 unit tests pass locally (no ROS2 on this
dev machine); 4 rclpy-dependent tests skip cleanly and need verification on
a real ROS2 (Jazzy) box, along with `colcon test` and the live-talker demo.

**Description**: A minimal CLI, `metawtf`, run with no arguments. On start it
reads a YAML config next to the package (default `metawtf.yaml`) declaring a set
of **columns** to sample. A timer fires at `sample_hz`; each tick prints one CSV
row to stdout: wall-clock timestamp plus one value per column. The same stream
is eyeballed live and redirected to a file (`> run.csv`) for spreadsheets and
graphing. v1 column type is `echo`: the latest value of a dotted-path field
from a topic.

Config schema (v1):
```yaml
sample_hz: 5.0          # rows per second (default 5.0)
columns:
  - name: odom_x        # column header (default: <topic>_<last field segment>)
    metric: echo
    topic: /odom
    type: nav_msgs/msg/Odometry   # optional; resolved from graph if omitted
    field: pose.pose.position.x
    stale_after: 2.0    # optional; blank cell if no msg within N sec (default: never)
```

Output:
```
time,odom_x,odom_z
12:00:01.200,1.203,0.044
12:00:01.400,1.210,0.043
```

Semantics and correctness rules (from studying `ros2 topic hz` / ros2cli):
- Subscriptions use graph-checked QoS: inspect `get_publishers_info_by_topic`;
  request RELIABLE only if *every* publisher offers RELIABLE, else BEST_EFFORT;
  TRANSIENT_LOCAL only if every publisher offers it, else VOLATILE (same rule
  as ros2cli's `choose_qos`). Wrong QoS silently delivers zero messages — this
  is the number one trap when subscribing to arbitrary topics.
- Message type from config `type`, else discovered from the graph; error on
  multi-type topics. If the topic isn't up at start, keep the column (empty
  cells) and retry subscription on a slow rescan timer.
- Echo value = field of the *latest* message at tick time ("last known value").
  Callbacks only extract and store scalars; all formatting/printing happens in
  the timer callback so subscription callbacks stay cheap (ros2 hz prints from
  a separate thread; we don't need one).
- Missing data (topic never published, stale, bad runtime path) → **empty CSV
  cell** — never 0, never a crash.
- Floats formatted `%.6g`; timestamp `HH:MM:SS.mmm`. Wall time everywhere
  (`time.monotonic()` for intervals); ROS/sim time deferred.

## How to Demo
**Setup**: A ROS2 graph publishing a topic named in `metawtf.yaml` (e.g. a demo
talker). Package built and sourced.

**Steps**:
1. Edit `metawtf.yaml` with echo columns for a live topic.
2. `ros2 run metawtf metawtf` (optionally `> run.csv`)

**Expected output**: A header row, then CSV rows at `sample_hz` with current
field values until Ctrl-C. The CSV imports into a spreadsheet as one plottable
series per column.

## Non-Goals (v1)
- hz and proc_cpu columns (F02, F03).
- Per-message printing (superseded by sampled rows).
- Command-line arguments (config path override deferred).
- Column set changing mid-run (F02 adds that, with header reprint); v1 columns
  are fixed from config.
- Indexing into message arrays (dotted attribute paths only).
- TUI / coloring / live graphs.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code until the user approves.
