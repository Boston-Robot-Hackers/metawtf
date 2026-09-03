# F02 — Topic rate (hz) columns by pattern

**Priority**: Medium
**Date Created:** 2026-07-16
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes

**Description**: Add `hz` columns to the sampled table. An entry selects one
topic (`topic:`) or many by regex (`match:`) against the live graph, with the
message type discovered from the graph, and reports received-message rate over
a rolling time `window`. The graph is rescanned periodically; topics that
appear after start add new columns (header is reprinted). Motivating case:
"hz for all topics starting with `/tf`."

Builds on F01:
```yaml
columns:
  - metric: hz
    match: "^/tf"       # regex on graph topic names
    window: 2.0         # rolling window, seconds (default 2.0; must be >= sample period)
  - metric: hz
    topic: /chatter     # single topic; column name = sanitized topic name
```

Output: one column per matched topic, e.g. `12:00:05.000,62.100,49.750`.
Column names are derived from topic names (leading `/` stripped, remaining `/`
→ `_`); `match` entries may not set `name`.

Correctness rules (from `ros2topic/verb/hz.py` and `ros2cli/qos.py`):
- Rate measures the **subscription receive rate**, from inter-arrival times
  recorded at callback time: over the arrivals inside `window`,
  rate = (n−1)/(t_newest − t_oldest); n < 2 → empty cell. Never computed from
  message header stamps. This is the same estimator ros2 hz uses
  (rate = 1/mean(Δt)) and — unlike naive count/window — it does not
  under-report at startup or for sparse topics.
- Arrival clock is `time.monotonic()` (wall). ros2 hz defaults to the ROS
  clock with `--wall-time` as opt-in; we deliberately invert that. Sim-time
  support deferred.
- Subscriptions are created with `raw=True`: count serialized messages, skip
  deserialization entirely (hz.py does the same when no filter is given).
  Critical when matching high-rate image/pointcloud topics.
- Same graph-checked QoS auto-selection as F01 — copied from `choose_qos`:
  RELIABLE only if all publishers are RELIABLE else BEST_EFFORT;
  TRANSIENT_LOCAL only if all publishers are TRANSIENT_LOCAL else VOLATILE.
- Rolling window: deque of arrival times, entries older than `window` pruned
  at each computation. (ros2 hz uses a count-based window, default 10000
  messages; ours is time-based to fit the fixed row cadence.)
- Matching runs against `get_topic_names_and_types`; multi-type topics are
  skipped with a warning.
- Column set may grow at rescan → a fresh header line is printed before the
  next row (documented caveat for spreadsheet import).

## How to Demo
**Setup**: A ROS2 graph publishing tf (e.g. robot bringup, or
`ros2 run tf2_ros static_transform_publisher ...`). Package built and sourced.

**Steps**:
1. Config with `- metric: hz` / `match: "^/tf"`.
2. `ros2 run metawtf metawtf`
3. While running, start a second tf-related publisher.

**Expected output**: Rows show measured rates for `/tf` (and `/tf_static`);
when the new publisher starts, a fresh header with the added column appears
and its rate fills in.

## Non-Goals (this feature)
- Glob syntax (regex only).
- Bandwidth/bytes, jitter, min/max interval — hz only.
- Count-based windows, per-publisher breakdown, sim-time rates.
- Removing columns for topics that vanish (their cells go empty).

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code until the user approves.
