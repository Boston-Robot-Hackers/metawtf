# TF01 — Config-driven sampled table trace, tasks for Feature F01
**Date Created:** 2026-07-16

Each step adds a test where feasible. Live-ROS steps keep rclpy usage fake/stub
friendly so the suite runs without a graph; real delivery is verified by demo.

## TF01.0 — Config schema: sample_hz + columns
**Status**: done — `metawtf/config.py`, tests in `test/test_config.py` (11
tests, all pass locally, no ROS dependency).
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

## TF01.1 — Message type resolution
**Status**: done — `metawtf/msg_type.py`. All 5 tests pass on ROS2 Jazzy,
including the `resolve_type_from_string` tests that previously skipped when
`rosidl_runtime_py` was absent.
**Description**: Resolve config `type` strings via
`rosidl_runtime_py.utilities.get_message`. When `type` is omitted, look the
topic up in the graph (`get_topic_names_and_types`): use its type, raise a
clear error on multi-type topics, report "not found" distinctly so the node
can retry later.
**Test**: Unit test — `std_msgs/msg/String` resolves to the class; bogus type
string raises; graph-lookup path tested with a fake names-and-types list
(found, multi-type, absent).

## TF01.2 — Dotted-path field extractor
**Status**: done — `metawtf/field_extract.py`, tests in
`test/test_field_extract.py` (4 tests, all pass locally).
**Description**: Given a message object and a dotted path
(`pose.pose.position.x`), return the value. Missing attribute → clear error.
Attribute paths only; no sequence indexing.
**Test**: Unit test against a constructed nested message — correct value
returned; bad path raises.

## TF01.3 — QoS auto-selection
**Status**: done — `metawtf/qos_select.py`. All 4 tests in
`test/test_qos_select.py` pass on ROS2 Jazzy.
**Description**: Helper that, given the publisher endpoint info list for a
topic, returns a QoSProfile: RELIABLE iff every publisher is RELIABLE else
BEST_EFFORT; TRANSIENT_LOCAL iff every publisher is TRANSIENT_LOCAL else
VOLATILE; empty publisher list → sensor_data-style default. Port of
`ros2cli.qos.choose_qos` without CLI args.
**Test**: Unit test with fake endpoint infos — all-reliable, mixed reliability,
all-best-effort, all-transient-local, mixed durability, zero publishers.

## TF01.4 — Echo column state
**Status**: done — `metawtf/echo_column.py`, tests in
`test/test_echo_column.py` (5 tests, all pass locally).
**Description**: Subscription callback extracts the configured field and stores
(value, monotonic arrival time). `sample(now)` returns the value, or None when
never seen or when `stale_after` has elapsed. Formatting: floats `%.6g`,
everything else `str()`.
**Test**: Unit test — inject fake messages, assert stored value; staleness with
a fake clock; exact format strings.

## TF01.5 — CSV sampler
**Status**: done — `metawtf/sampler.py`, tests in `test/test_sampler.py`
(2 tests, all pass locally).
**Description**: Timer callback at `sample_hz` builds one row from column
states: first column `time` as `HH:MM:SS.mmm`, then one cell per column
(empty for None). Prints the header once before the first row. Column order
fixed from config.
**Test**: Unit test with fake columns and captured stdout — exact header and
row strings; None → empty cell.

## TF01.6 — Node wiring, lazy subscribe, CLI
**Status**: done — `metawtf/tracer_node.py`, `console_scripts` entry in
`setup.py`. Tests in `test/test_tracer_node.py` pass on ROS2 Jazzy; the node
builds and runs via `ros2 run metawtf metawtf`. Config is resolved next to the
installed module (`default_config_path`), installed via `package_data`.
**Description**: TracerNode: per echo column resolve type (config or graph),
create the subscription with auto QoS; if the topic is absent, retry on a
1 Hz rescan timer so late topics still connect. `main()`: load config,
`rclpy.init`, spin until Ctrl-C, clean shutdown. Register console_script
`metawtf` in `setup.py`.
**Test**: Unit-test the callback path directly (inject fake message); smoke
test that the node constructs and destroys cleanly under a real
`rclpy.init()`/`shutdown()` with no publishers. End-to-end DDS delivery is
covered by the demo, not the suite — noted here as the reason.

## TF01.7 — Feature test suite + demo verification
**Status**: done — on ROS2 Jazzy, `python3 -m pytest test/` reports 34 passed
(the style guide's plain-pytest gate; `colcon test` has a separate discovery
quirk, tracked as a chore). Live demo: published `/chatter` at 5 Hz and ran
`ros2 run metawtf metawtf` → header printed once, rows at `sample_hz`, empty
cells before first message, then the echoed value. Sample `metawtf.yaml` lives
next to the module.
**Description**: TF01.0–TF01.6 pass together; add a sample `metawtf.yaml`; run the
F01 demo against a live talker; redirect to a file and confirm it imports as
clean CSV.
**Test**: `colcon test --packages-select metawtf` green; demo produces header +
rows at the configured rate.
