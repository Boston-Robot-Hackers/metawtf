# TF01 — Config-driven topic trace, tasks for Feature F01

Each step adds a test where feasible. Live-ROS steps use fake/stub messages so
tests run without a running graph.

## T01 — Load and validate YAML config
**Status**: not done
**Description**: Find `metawtf.yaml` next to the package, parse it, validate the
schema (`topics` list; each entry has `topic`, `type`, `fields`). Clear error on
missing file or bad schema.
**Test**: Unit test with sample YAML strings — valid config parses to expected
structure; missing keys and malformed YAML raise clear errors.

## T02 — Resolve message type from string
**Status**: not done
**Description**: Turn a `type` string like `nav_msgs/msg/Odometry` into the
importable rclpy message class.
**Test**: Unit test resolving a known message type (e.g. `std_msgs/msg/String`)
returns the class; bad type string raises a clear error.

## T03 — Dotted-path field extractor
**Status**: not done
**Description**: Given a message object and a dotted path (`pose.pose.position.x`),
return the value. Handle missing attributes with a clear error.
**Test**: Unit test against a constructed nested message / simple object —
correct value returned; bad path raises.

## T04 — Line formatter
**Status**: not done
**Description**: Format one output line: `HH:MM:SS.mmm <topic> field=val ...`
from topic name, timestamp, and extracted field values.
**Test**: Unit test — given fixed inputs, exact expected string.

## T05 — Tracer node wiring
**Status**: not done
**Description**: rclpy node that, per config entry, creates a subscription to the
topic with the resolved type; callback extracts fields, formats, prints.
**Test**: Unit test the callback in isolation (inject a fake message, assert
printed line via captured stdout). Full graph subscription covered by demo, not
unit test — note: needs live ROS.

## T06 — CLI entry point
**Status**: not done
**Description**: `main()` with no args: load config, build node, spin until
Ctrl-C, clean shutdown. Register console_script in `setup.py`.
**Test**: Smoke test that `main` loads config and constructs the node without
spinning (spin/rclpy.init patched or guarded). Note why full run is demo-only.

## T07 — Feature test suite + demo verification
**Status**: not done
**Description**: Ensure T01–T06 tests pass together; add a sample `metawtf.yaml`;
run the F01 demo against a live/demo topic to confirm real output.
**Test**: `colcon test --packages-select metawtf` green; demo step produces
scrolling lines.
