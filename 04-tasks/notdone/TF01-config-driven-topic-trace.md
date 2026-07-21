# TF01 — Config-driven sampled table trace, tasks for Feature F01

Each step adds a test where feasible. Live-ROS steps keep rclpy usage fake/stub
friendly so the suite runs without a graph; real delivery is verified by demo.

## T01 — Config schema: sample_hz + columns
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

## T02 — Message type resolution
**Status**: code done, tests partially verified — `metawtf/msg_type.py`.
Graph-lookup path (`resolve_type_string_from_graph`) is pure and passes 3
tests locally. `resolve_type_from_string` needs `rosidl_runtime_py`, not
installed in this dev environment; its 2 tests are written with
`pytest.importorskip` and currently skip. Needs verification on a real
ROS2 install.
**Description**: Resolve config `type` strings via
`rosidl_runtime_py.utilities.get_message`. When `type` is omitted, look the
topic up in the graph (`get_topic_names_and_types`): use its type, raise a
clear error on multi-type topics, report "not found" distinctly so the node
can retry later.
**Test**: Unit test — `std_msgs/msg/String` resolves to the class; bogus type
string raises; graph-lookup path tested with a fake names-and-types list
(found, multi-type, absent).

## T03 — Dotted-path field extractor
**Status**: done — `metawtf/field_extract.py`, tests in
`test/test_field_extract.py` (4 tests, all pass locally).
**Description**: Given a message object and a dotted path
(`pose.pose.position.x`), return the value. Missing attribute → clear error.
Attribute paths only; no sequence indexing.
**Test**: Unit test against a constructed nested message — correct value
returned; bad path raises.

## T04 — QoS auto-selection
**Status**: code done, tests unverified — `metawtf/qos_select.py`. Needs
`rclpy.qos`, not installed in this dev environment. 4 tests written in
`test/test_qos_select.py` with `pytest.importorskip`; currently skip.
Needs verification on a real ROS2 install.
**Description**: Helper that, given the publisher endpoint info list for a
topic, returns a QoSProfile: RELIABLE iff every publisher is RELIABLE else
BEST_EFFORT; TRANSIENT_LOCAL iff every publisher is TRANSIENT_LOCAL else
VOLATILE; empty publisher list → sensor_data-style default. Port of
`ros2cli.qos.choose_qos` without CLI args.
**Test**: Unit test with fake endpoint infos — all-reliable, mixed reliability,
all-best-effort, all-transient-local, mixed durability, zero publishers.

## T05 — Echo column state
**Status**: done — `metawtf/echo_column.py`, tests in
`test/test_echo_column.py` (5 tests, all pass locally).
**Description**: Subscription callback extracts the configured field and stores
(value, monotonic arrival time). `sample(now)` returns the value, or None when
never seen or when `stale_after` has elapsed. Formatting: floats `%.6g`,
everything else `str()`.
**Test**: Unit test — inject fake messages, assert stored value; staleness with
a fake clock; exact format strings.

## T06 — CSV sampler
**Status**: done — `metawtf/sampler.py`, tests in `test/test_sampler.py`
(2 tests, all pass locally).
**Description**: Timer callback at `sample_hz` builds one row from column
states: first column `time` as `HH:MM:SS.mmm`, then one cell per column
(empty for None). Prints the header once before the first row. Column order
fixed from config.
**Test**: Unit test with fake columns and captured stdout — exact header and
row strings; None → empty cell.

## T07 — Node wiring, lazy subscribe, CLI
**Status**: code done, tests unverified — `metawtf/tracer_node.py`,
`console_scripts` entry added in `setup.py`. Needs `rclpy`, not installed
in this dev environment. 2 tests written in `test/test_tracer_node.py`
with `pytest.importorskip`; currently skip. Needs verification (build +
smoke test) on a real ROS2 install.
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
**Status**: not done — blocked on a real ROS2 (Jazzy) environment. This
dev machine has no `ros2`, no `rclpy`, no `~/ros2_ws`. 25/29 unit tests
pass locally (pure logic); 4 are ROS-dependent and skip cleanly rather
than fail. `colcon test` and the live-talker demo still need to run on
the actual ROS2 box. Sample `metawtf.yaml` added at repo root.
**Description**: T01–T07 pass together; add a sample `metawtf.yaml`; run the
F01 demo against a live talker; redirect to a file and confirm it imports as
clean CSV.
**Test**: `colcon test --packages-select metawtf` green; demo produces header +
rows at the configured rate.
