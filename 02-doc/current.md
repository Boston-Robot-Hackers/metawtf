# Current Status — Session Handoff

**Last updated:** 2026-07-21

## State
TF01 (F01) implemented: `metawtf/config.py`, `field_extract.py`, `msg_type.py`,
`qos_select.py`, `echo_column.py`, `sampler.py`, `tracer_node.py`, plus
`console_scripts` entry and a sample `metawtf.yaml`. T01, T03, T05, T06 done
and verified (pure-logic unit tests, no ROS dependency). T02, T04, T07 code
written but unverified — this dev machine has **no ROS2 install at all**
(`rclpy`, `ros2`, `~/ros2_ws` all absent), so their tests are written with
`pytest.importorskip` and currently skip rather than run. T08 (full suite +
demo) is blocked on that verification.

## Next Steps
1. On a real ROS2 (Jazzy) box: `colcon build`, run `colcon test`, confirm the
   4 skipped tests (`test_qos_select.py`, `test_tracer_node.py`, and the two
   `resolve_from_string` tests in `test_msg_type.py`) pass for real.
2. Run the F01 demo against a live talker (see feature file) and close out
   T02/T04/T07/T08, then move F01/TF01 to `done/`.
3. Then get plan approval for F02/TF02, F03/TF03 per their Process Gates.

## Open Questions
- None.
