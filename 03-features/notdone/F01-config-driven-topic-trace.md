# F01 — Config-driven topic trace

**Priority**: High
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no

**Description**: A minimal CLI, `metawtf`, run with no arguments. On start it reads
a YAML config file stored alongside the package (default `metawtf.yaml`). The
config lists ROS2 topics to trace, each with its message type and the fields to
show. The tool subscribes to every listed topic and, as messages arrive, prints
one scrolling text line per message: timestamp, topic name, and the selected
field values. Runs until Ctrl-C. No TUI, no elaborate formatting — those come
later as needs arise.

Scope for v1:
- Single config file, YAML, discovered next to the executable/package.
- Config schema (minimal):
  ```yaml
  topics:
    - topic: /odom
      type: nav_msgs/msg/Odometry
      fields: [pose.pose.position.x, pose.pose.position.y]
    - topic: /scan
      type: sensor_msgs/msg/LaserScan
      fields: [range_min, range_max]
  ```
- Message type resolved dynamically from the `type` string.
- Fields addressed by dotted path into the message object.
- Output: plain stdout, one line per received message.

## How to Demo
**Setup**: A ROS2 graph publishing at least one topic named in `metawtf.yaml`
(e.g. run a demo talker or a rosbag). Package built and sourced.

**Steps**:
1. Edit `metawtf.yaml` to list a live topic, its type, and a couple of fields.
2. `ros2 run metawtf metawtf`

**Expected output**: Scrolling lines like
`12:00:01.234 /odom pose.pose.position.x=1.20 pose.pose.position.y=0.05`,
one per received message, until Ctrl-C.

## Non-Goals (v1)
- Command-line arguments beyond none (config path override deferred).
- TUI / in-place refresh / coloring.
- Rates, health, TF, node/param state.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code until the user approves.
