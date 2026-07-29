# F10 — multi-field echo columns
**Priority**: Medium
**Done:** no
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Note:** code + unit tests complete (232 pass); live `/cmd_vel` demo pending
user verification, then move to `done/`.
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
