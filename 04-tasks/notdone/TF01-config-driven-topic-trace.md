# TF01 — Config-driven sampled table trace, tasks for Feature F01

Each step adds a test where feasible. Live-ROS steps keep rclpy usage fake/stub
friendly so the suite runs without a graph; real delivery is verified by demo.

## T01 — Config schema: sample_hz + columns
**Status**: not done
**Description**: Load `metawtf.yaml` next to the package. Parse top-level
`sample_hz` (default 5.0, must be > 0) and `columns` list. An echo entry
requires `topic` and `field`; optional `name` (default
`<sanitized topic>_<last field segment>`, e.g. `odom_x`), optional `type`,
optional `stale_after` (seconds > 0). Unknown keys, missing required keys, and
wrong types produce clear errors. Unknown `metric` values → clear error (hz,
proc_cpu arrive in F02/F03).
**Test**: Unit tests over YAML strings — valid configs parse to expected
structs; missing `field`, non-numeric `sample_hz`, unknown key, bad `metric`
each raise a clear error.

## T02 — Message type resolution
**Status**: not done
**Description**: Resolve config `type` strings via
`rosidl_runtime_py.utilities.get_message`. When `type` is omitted, look the
topic up in the graph (`get_topic_names_and_types`): use its type, raise a
clear error on multi-type topics, report "not found" distinctly so the node
can retry later.
**Test**: Unit test — `std_msgs/msg/String` resolves to the class; bogus type
string raises; graph-lookup path tested with a fake names-and-types list
(found, multi-type, absent).

## T03 — Dotted-path field extractor
**Status**: not done
**Description**: Given a message object and a dotted path
(`pose.pose.position.x`), return the value. Missing attribute → clear error.
Attribute paths only; no sequence indexing.
**Test**: Unit test against a constructed nested message — correct value
returned; bad path raises.

## T04 — QoS auto-selection
**Status**: not done
**Description**: Helper that, given the publisher endpoint info list for a
topic, returns a QoSProfile: RELIABLE iff every publisher is RELIABLE else
BEST_EFFORT; TRANSIENT_LOCAL iff every publisher is TRANSIENT_LOCAL else
VOLATILE; empty publisher list → sensor_data-style default. Port of
`ros2cli.qos.choose_qos` without CLI args.
**Test**: Unit test with fake endpoint infos — all-reliable, mixed reliability,
all-best-effort, all-transient-local, mixed durability, zero publishers.

## T05 — Echo column state
**Status**: not done
**Description**: Subscription callback extracts the configured field and stores
(value, monotonic arrival time). `sample(now)` returns the value, or None when
never seen or when `stale_after` has elapsed. Formatting: floats `%.6g`,
everything else `str()`.
**Test**: Unit test — inject fake messages, assert stored value; staleness with
a fake clock; exact format strings.

## T06 — CSV sampler
**Status**: not done
**Description**: Timer callback at `sample_hz` builds one row from column
states: first column `time` as `HH:MM:SS.mmm`, then one cell per column
(empty for None). Prints the header once before the first row. Column order
fixed from config.
**Test**: Unit test with fake columns and captured stdout — exact header and
row strings; None → empty cell.

## T07 — Node wiring, lazy subscribe, CLI
**Status**: not done
**Description**: TracerNode: per echo column resolve type (config or graph),
create the subscription with auto QoS; if the topic is absent, retry on a
1 Hz rescan timer so late topics still connect. `main()`: load config,
`rclpy.init`, spin until Ctrl-C, clean shutdown. Register console_script
`metawtf` in `setup.py`.
**Test**: Unit-test the callback path directly (inject fake message); smoke
test that the node constructs and destroys cleanly under a real
`rclpy.init()`/`shutdown()` with no publishers. End-to-end DDS delivery is
covered by the demo, not the suite — noted here as the reason.

## T08 — Feature test suite + demo verification
**Status**: not done
**Description**: T01–T07 pass together; add a sample `metawtf.yaml`; run the
F01 demo against a live talker; redirect to a file and confirm it imports as
clean CSV.
**Test**: `colcon test --packages-select metawtf` green; demo produces header +
rows at the configured rate.
