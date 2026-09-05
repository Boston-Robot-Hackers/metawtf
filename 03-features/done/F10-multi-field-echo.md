# F10 — multi-field echo columns
**Priority**: Medium
**Date Created:** 2026-07-29
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Note:** live `/cmd_vel` demo verified by Pito 2026-09-05: two columns
`cmd_vel_linear_x` and `cmd_vel_angular_z` tracked correctly from one
subscription. Full suite not runnable on this machine (no ROS2 install), so
verified with the ROS2-independent subset: 228 passed, 4 skipped; the 10
tests requiring `rosidl_runtime_py` (pre-existing dependency since TF01,
unrelated to F10) are unreachable here.
**Description**: One `echo` line can name several message field paths with
a comma list in `field=`, producing one column per path from a single
subscription. Mirrors `subfields=` but for real message fields, not keys inside
a JSON string. Solves the common case of a `Twist` on `/cmd_vel` where you want
`linear.x` and `angular.z` side by side without two `echo` lines.

Syntax and rules (singular keywords only — no `fields`/`names`):
- `echo /cmd_vel field=linear.x,angular.z` — a comma list in `field=` gives one
  subscription, one column per path.
- A single-path `field=` is the plain single-column echo (unchanged behavior).
- A multi-path `field=` cannot combine with `json=`/`subfields=` (those split
  one JSON string field, not several message fields).
- Multi-column headers auto-derive as `<sanitized topic>_<path with dots as
  underscores>`; a `name=` comma list (one per column, count must match)
  overrides them. A single-field echo's `name=` is one string (default:
  sanitized topic).
- `width=` on a multi-field/`subfields` echo is a comma list, one width per
  column; omitted defaults each to `DEFAULT_ECHO_WIDTH`.

## How to Demo
**Setup**: `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist` with nonzero
`linear.x` and `angular.z`; a `metawtf.conf` containing
`echo /cmd_vel field=linear.x,angular.z`.

**Steps**:
1. Run `metawtf`.
2. Watch the trace.

**Expected output**: two columns `cmd_vel_linear_x` and `cmd_vel_angular_z`
tracking their respective values, fed by one `/cmd_vel` subscription.
