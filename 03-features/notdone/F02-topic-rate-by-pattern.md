# F02 — Topic rate (hz) by pattern

**Priority**: Medium
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no

**Description**: Extend metawtf with a rate metric. Config entries may select
topics by a name pattern (regex) rather than an explicit topic, and request the
`hz` metric instead of field echo. The tool resolves matching topics from the
live ROS2 graph, subscribes to each (message type discovered from the graph, not
the config), counts messages over a rolling window, and prints each topic's rate
periodically. Motivating case: "hz for all topics starting with `tf`."

Builds on F01. Unified entry schema — an entry is either echo (F01) or hz (F02):
```yaml
metrics:
  - match: "^/tf"        # regex on topic name
    metric: hz
    window: 5.0          # seconds, averaging window (default 5.0)
  - topic: /cmd_vel      # F01-style echo entry still valid
    metric: echo
    fields: [linear.x, angular.z]
```

Scope for v1 of this feature:
- `match` = regex against topic names from the graph.
- Message type resolved from the graph (`get_topic_names_and_types`).
- Graph rescanned periodically so topics appearing after start are picked up.
- `hz` = messages counted per rolling `window`, printed on a timer.
- Output line, e.g. `12:00:05 /tf 62.1 hz (312 msgs / 5.0s)`.

## How to Demo
**Setup**: A ROS2 graph publishing `tf` topics (e.g. any robot bringup, or
`ros2 run tf2_ros static_transform_publisher ...`). Package built and sourced.

**Steps**:
1. Config with `- match: "^/tf"` / `metric: hz`.
2. `ros2 run metawtf metawtf`

**Expected output**: Every `window` seconds, one line per matched topic showing
its measured rate, updating as traffic changes; new matching topics appear when
they start publishing.

## Non-Goals (this feature)
- Glob syntax (regex only for now).
- Bandwidth/bytes, jitter, min/max interval — hz only.
- TUI / in-place refresh (still scrolling text).

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code until the user approves.
