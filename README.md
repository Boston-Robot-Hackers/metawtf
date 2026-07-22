# metawtf

A minimal ROS2 CLI that samples selected topic fields into a CSV stream on
stdout — one row per tick — so you can eyeball live values and redirect the
same output to a file for spreadsheets and graphing.

## Installation

```bash
cd ~/ros2_ws
colcon build --packages-select metawtf
source install/setup.bash
```

The build installs a `metawtf` command onto your PATH, so no `ros2 run` is
needed. It stays available in any shell where the workspace is sourced.

## Usage

```bash
metawtf            # prints CSV rows to the terminal
metawtf > run.csv  # capture for a spreadsheet
```

On start it reads `metawtf.yaml` from the **current working directory**. Edit it
and re-run — no rebuild needed. (`metawtf/metawtf.yaml` in the repo is a sample
to copy.)

**To quit:** press `q` (no Enter needed) or `Ctrl-C`. It shuts down cleanly with
no traceback. When stdin is not a terminal (e.g. piped), only `Ctrl-C` applies.

### Configuration reference

Any key not listed below is rejected with a clear error at startup.

```yaml
sample_hz: 5.0            # rows per second (default 5.0)
time:                     # optional; configures the leading timestamp column
  format: "%H:%M:%S"      # optional strftime; default keeps HH:MM:SS.mmm
  width: 12               # optional; min column width
columns:
  - name: odom_x          # column header (default: <topic>_<last field segment>)
    metric: echo
    topic: /odom
    field: pose.pose.position.x
    type: nav_msgs/msg/Odometry   # optional; resolved from the graph if omitted
    stale_after: 2.0      # optional; blank cell if no msg within N seconds
    width: 10             # optional; min column width
  - metric: hz            # message receive rate
    match: "^/tf"         # regex over graph topics; one column per match
    window: 2.0           # optional rolling window (default 2.0, >= sample period)
```

#### Top level

| Key         | Required | Type   | Default | Rules                    |
|-------------|----------|--------|---------|--------------------------|
| `sample_hz` | no       | number | `5.0`   | must be > 0              |
| `columns`   | yes      | list   | —       | must be a non-empty list |
| `time`      | no       | map    | —       | see below                |

#### `time` block (the leading timestamp column)

| Key      | Required | Type   | Default          | Rules                                             |
|----------|----------|--------|------------------|---------------------------------------------------|
| `format` | no       | string | `HH:MM:SS.mmm`   | Python `strftime`; the default keeps millisecond precision (which strftime cannot express) |
| `width`  | no       | int    | natural width    | must be > 0; pads the column to a minimum width   |

#### `echo` column keys

Reports the latest value of a message field, sampled at each tick.

| Key           | Required | Type   | Default                          | Rules                                             |
|---------------|----------|--------|----------------------------------|---------------------------------------------------|
| `metric`      | yes      | string | —                                | must be `echo`                                    |
| `topic`       | yes      | string | —                                | non-empty; the topic to subscribe to             |
| `field`       | yes      | string | —                                | dotted attribute path, e.g. `pose.pose.position.x`; no array indexing |
| `name`        | no       | string | sanitized topic                  | the CSV column header                             |
| `type`        | no       | string | resolved from the graph          | e.g. `nav_msgs/msg/Odometry`; needed only if the topic isn't up at start or is multi-type |
| `stale_after` | no       | number | never stale                      | must be > 0; blank the cell if no message arrives within this many seconds |
| `width`       | no       | int    | natural width                    | must be > 0; pads the cell to a minimum width     |

A bad `field` path (e.g. a typo) does not crash the trace: that cell shows `?`
until a readable message arrives.

#### `hz` column keys

Reports the rolling message receive rate (`ros2 topic hz`-style span estimate),
formatted `%.3f`. Give exactly one of `topic` or `match`.

| Key      | Required | Type   | Default            | Rules                                             |
|----------|----------|--------|--------------------|---------------------------------------------------|
| `metric` | yes      | string | —                  | must be `hz`                                       |
| `topic`  | one-of   | string | —                  | a single topic; column name defaults to the sanitized topic |
| `match`  | one-of   | string | —                  | regex over graph topic names; one column per matched topic, added live as topics appear |
| `window` | no       | number | `2.0`              | rolling window in seconds; must be >= the sample period |
| `name`   | no       | string | sanitized topic    | allowed with `topic`; **forbidden** with `match`   |
| `width`  | no       | int    | natural width      | must be > 0; pads the cell to a minimum width      |

Notes:
- A default `name` (echo or hz, single-topic or per-`match`-topic) strips the
  leading `/` and turns remaining `/` into `_` (so `/robot/scan` →
  `robot_scan`). Give two echo columns on the same topic explicit names to tell
  them apart.
- `field` is an attribute path only; indexing into message arrays is not
  supported in this version.
- A `match` column set can grow at runtime; when a new topic is discovered a
  fresh header line is printed before the next row (a documented CSV caveat).

### Output

Each tick prints the timestamp column plus one value per column. Missing, stale,
or not-yet-published data produces an **empty cell** — never `0`, never a crash.
Floats are formatted `%.6g`. `width` is a **minimum**: shorter cells are
space-padded, but a value longer than `width` is printed in full (never
truncated), so it overflows and nudges that row's later columns out of
alignment until the next row. Cells stay comma-delimited, so the output still
imports as CSV.

```
time,odom_x,odom_z
12:00:01.200,,
12:00:01.400,1.210,0.043
```

## Development

Tests run with plain `pytest` (no `colcon test` dependency); source ROS2 first
so the `rclpy`-dependent tests run rather than skip:

```bash
source /opt/ros/jazzy/setup.bash
python3 -m pytest test/ -v
```

## License

MIT — see [LICENSE](LICENSE)
