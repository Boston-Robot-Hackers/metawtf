# metawtf

A minimal ROS2 CLI that samples selected topic fields into a CSV stream on
stdout — one row per tick — so you can eyeball live values and redirect the
same output to a file for spreadsheets and graphing.

## How is this different from `ros2 bag`?

They overlap only in that both watch topics. `ros2 bag` is a flight recorder:
it stores *every* raw message on the selected topics, serialized, for later
replay or offline analysis. High fidelity — but unreadable while recording,
and turning it into "just `pose.position.x` as a plottable series" takes
post-processing.

metawtf is a live, deliberately lossy, pre-shaped view:

- **Time-aligned columns.** Topics publishing at different rates are resampled
  onto a shared clock, one row per tick, so their values are directly
  comparable and plottable. A bag keeps each message's own timestamp;
  alignment is your problem later.
- **Watchable while it runs.** `ros2 topic echo` legibility with multi-topic
  breadth — eyeball values live, or redirect the same stream to a file.
- **Derived values.** `hz` columns compute receive rates; `json: true` reaches
  inside a JSON string carried in a message field. A bag just stores bytes.
- **Tiny output, zero post-processing.** Last-known-value sampling at a few Hz
  produces a CSV a spreadsheet opens directly.

Rule of thumb: if you don't yet know which fields you'll need, record a bag —
metawtf can't recover data it didn't sample. If you know exactly which scalars
you want to watch or graph *right now*, that's metawtf.

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
metawtf                  # prints CSV rows to the terminal
metawtf > run.csv        # capture for a spreadsheet
metawtf -f other.yaml    # use a config other than ./metawtf.yaml
metawtf -h               # show help and exit
```

On start it reads `metawtf.yaml` from the **current working directory** (or the
file given with `-f`). Edit it and re-run — no rebuild needed.
(`metawtf/metawtf.yaml` in the repo is a sample to copy.)

**Keys while running** (no Enter needed): `space` pauses/resumes row output,
`h` shows help, `q` quits (`Ctrl-C` also works). It shuts down cleanly with no
traceback. When stdin is not a terminal (e.g. piped), only `Ctrl-C` applies.

### Configuration reference

Any key not listed below is rejected with a clear error at startup.

```yaml
sample_hz: 5.0            # rows per second (default 5.0)
time:                     # optional; configures the leading timestamp column
  format: "%H:%M:%S"      # optional strftime; default keeps HH:MM:SS.mmm
  width: 12               # optional; min column width
columns:
  - name: odom_x          # column header (default: sanitized topic)
    metric: echo
    topic: /odom
    field: pose.pose.position.x
    type: nav_msgs/msg/Odometry   # optional; resolved from the graph if omitted
    stale_after: 2.0      # optional; blank cell if no msg within N seconds
    width: 10             # optional; min column width
  - metric: echo          # a JSON string inside a field, one column per key
    topic: /explore/status
    field: data
    json: true
    subfields: [reached, failed]  # omit to expand all top-level keys
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
| `json`        | no       | bool   | `false`                          | parse the extracted field as a JSON string before selecting |
| `subfields`   | no       | list   | all top-level keys               | requires `json: true`; dotted keys reach nested objects (`payload.count`) |

A bad `field` path (e.g. a typo) does not crash the trace: that cell shows `?`
until a readable message arrives.

#### JSON subfields (`json: true`)

Some topics carry structured data as a JSON string inside a single field
(e.g. `/explore/status`, a `std_msgs/msg/String` whose `data` is
`{"state": "idle", "reached": 0, "failed": 0}`). With `json: true`, one config
entry expands into one plottable column per selected key:

- Column names are `<sanitized topic>_<key with dots as underscores>`
  (`explore_status_reached`). An explicit `name` is allowed only when
  `subfields` selects a single key; with several keys it is a config error.
- Omitting `subfields` expands to all top-level keys of the **first parsed
  message**, in order; the column set is then fixed (later extra keys are
  ignored, missing keys show `?`).
- Malformed JSON, a missing key, or a key resolving to an object/array/null
  shows `?` in that cell — never a crash — and recovers on the next
  well-formed message. Only scalars (string/number/bool) are rendered.
- `json` is valid only on `echo` columns.

#### `hz` column keys

Reports the rolling message receive rate (`ros2 topic hz`-style span estimate),
formatted with 2 decimals. Give exactly one of `topic` or `match`.

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
Floats are formatted with **2 decimals**. `width` is a **minimum**: the comma
sits right after each value and shorter cells are space-padded after it, so
columns line up in the terminal; a value longer than `width` is printed in full
(never truncated), so it overflows and nudges that row's later columns out of
alignment until the next row. The output still imports as CSV: any cell
containing a comma, quote, or newline is quoted per RFC 4180 (inner quotes
doubled), so string values always occupy a single cell.

```
time,          odom_x,    odom_z
12:00:01.200,  ,
12:00:01.400,  1.21,      0.04
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
