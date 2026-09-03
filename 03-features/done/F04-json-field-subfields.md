# F04 — JSON-string fields expanded into subfield columns

**Priority**: Medium
**Date Created:** 2026-07-22
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes

**Description**: Some topics carry structured data as a JSON string inside a
single message field rather than as native ROS submessage fields. The
motivating case is `/explore/status` (`std_msgs/msg/String`) whose `data` is
`{"state": "idle", "reached": 0, "failed": 0}`. Echoing `field: data` today
dumps the whole `{...}` blob into one unplottable cell.

This feature extends the `echo` metric so a JSON-string field can be parsed and
selected: one config entry expands into one column per chosen JSON key, each a
plottable scalar on the shared sampled rows.

Config (builds on F01 echo):
```yaml
columns:
  - metric: echo
    topic: /explore/status
    field: data              # the field holding the JSON string
    json: true               # parse that string as JSON before selecting
    subfields: [reached, failed]   # keys to pull out; omit = all top-level keys
```

Output:
```
time,explore_status_reached,explore_status_failed
13:20:01.200,0,0
13:20:01.400,3,1
```

Semantics and correctness rules:
- `json: true` is opt-in. Without it, `field` behaves exactly as in F01 (the
  raw value, no parsing) — no auto-detection of "looks like JSON", to avoid
  guessing.
- `field` first resolves as a normal dotted ROS attribute path (usually just
  `data`) to obtain the string; that string is then parsed with `json.loads`.
- `subfields` selects keys. Each becomes its own column; entries may be dotted
  to reach into nested JSON objects (`payload.count`). Omitting `subfields`
  expands to all top-level keys of the object (order preserved from the first
  parsed message; documented caveat if keys vary between messages).
- Column naming: `<sanitized topic>_<key-with-dots-as-underscores>`
  (`explore_status_reached`). Because one entry yields multiple columns, an
  explicit `name` is forbidden when `subfields` has more than one key (same rule
  as hz `match`). A single-key selection may set `name`.
- Per-cell error handling reuses F01's rule: a message whose `data` is not valid
  JSON, or is missing a selected key, or whose selected value is not a scalar
  (object/array/null), renders that cell as `?` — never a crash — and recovers
  when a later message is well-formed. Empty cell before the first message.
- Only scalars (str/int/float/bool) are plottable; a key resolving to an object
  or array is `?`, not a stringified blob.
- `json` is only valid on `echo` columns; `json: true` with `metric: hz` is a
  config error.

## How to Demo
**Setup**: A node publishing a JSON-string topic. If `/explore/status` isn't
live, publish a stand-in to a **non-real** topic (never a real robot topic):
`ros2 topic pub -r 2 /mw_demo_status std_msgs/msg/String '{data: "{\"state\": \"idle\", \"reached\": 3, \"failed\": 1}"}'`

**Steps**:
1. Config with an echo column: `topic: /mw_demo_status`, `field: data`,
   `json: true`, `subfields: [reached, failed]`.
2. `metawtf` (from a directory containing that `metawtf.yaml`).

**Expected output**: Header `time,mw_demo_status_reached,mw_demo_status_failed`
then rows with the numeric values; a malformed message shows `?` in those cells.

## Non-Goals (this feature)
- YAML/other embedded encodings — JSON only.
- Array indexing into JSON arrays (dotted object keys only, mirroring the ROS
  attribute-path non-goal).
- Native ROS submessage-branch expansion (selecting several fields under
  `pose.pose.position`) — a natural follow-on, deferred to keep this scoped to
  the JSON case.
- Rewriting hz/proc_cpu to support `subfields`.

## Follow-ups
- **All-fields expansion for plain messages** (deferred from Non-Goals above):
  the `JsonKeysExpander` grows one column per key of the first parsed JSON
  message; the same trick could grow one column per scalar field of any
  message type, driven by the type's slot/field definitions instead of parsed
  JSON. Sketch:
  ```yaml
  - metric: echo
    topic: /cmd_vel
    all_fields: true   # -> columns cmd_vel_linear_x ... cmd_vel_angular_z
  ```
  (Alternative spellings: `field: "*"`, or make `field` optional and treat its
  absence as "all".) Nested submessages expand recursively as dotted paths
  (`linear.x`); non-scalar slots (arrays, nested blobs) render `?` or are
  skipped, same rules as the JSON case. Column naming follows the F04 pattern
  (sanitized topic + dots-as-underscores). No task file yet — promote to F05
  if wanted.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code until the user approves.
