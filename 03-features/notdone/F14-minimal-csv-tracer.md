# F14 — Minimal CSV tracer

**Priority**: Medium
**Date Created:** 2026-10-22
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no

**Description**: Reduce tracked production runtime and installer code by at
least 50% from a baseline of 2,076 physical lines (target: 1,038 or fewer),
while retaining a useful ROS2 trace workflow and tests for all retained
behavior. The proposed smaller product keeps configured topic-field sampling,
timestamps, CSV output, and the installer. It removes process/system CPU
metrics, topic-rate and regex-discovery columns, JSON-specific extraction and
dynamic expansion, human terminal formatting/pinned headers, column widths,
and interactive keyboard controls. Update the spec and user documentation to
make the reduced contract explicit; do not preserve obsolete behavior only for
the sake of old tests.

## How to Demo

**Setup**: ROS2 sourced, metawtf installed in a colcon workspace, and a
publishing topic with a scalar field.

**Steps**:
1. Configure one `echo` column for the topic and field.
2. Run `metawtf` with stdout redirected to a CSV file.
3. Open the file in a spreadsheet or inspect its timestamped rows.

**Expected output**: One timestamped CSV row per sample tick, with the latest
configured topic-field value.

## Process Gate

After creating this feature file and its matching task file, stop and present
the complete plan. Do not change implementation files until the user approves.
