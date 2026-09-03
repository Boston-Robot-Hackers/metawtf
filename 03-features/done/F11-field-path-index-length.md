# F11 — array indexing and length in field paths
**Priority**: High
**Date Created:** 2026-09-03
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Note:** All 7 tasks (TF11.0–TF11.6) done, including the live
`/oak/detections` demo (verified by Pito, 2026-09-03): `ntrk` reads live
track count, `0` (not `?`) on an empty frame, recovers on re-detection.
**Description**: Two new segment forms in a field path — an *index* and a
*length* — so array-valued message fields become reachable. Nothing else.

## Why

Today `extract_field` walks a dotted path with `getattr` and nothing else:

- any array-valued field is unreachable — `detections[0].id` fails
- so is any "how many are there" question

The motivating case is `dome_vision`'s `load.conf`, the one-timeline dashboard
for issue `I02` (OAK undervoltage hard reset).

That dashboard already shows host CPU, chip temperature, Leon core load and
delivered topic rates — but **not live track count**, the one number that says
whether the tracker is the load peak.

`detections.#` is that number.

## Syntax

Two segment forms extend the existing dotted path:

- **Index** — `[N]` on a segment: `detections[0].results[0].hypothesis.score`.
  `N` is an integer; **negative counts from the end**, so `[-1]` is the last.
- **Length** — a `#` segment, **final position only**: `detections.#` yields
  `len(detections)`.

Both are whitespace-free and comma-free, so **the tokenizer and the F10
comma-list fan-out need no change**.

`field=detections.#,detections[0].id` is already two columns from one
subscription.

`#` is safe mid-token: the grammar comments only a line whose *first* non-space
character is `#`.

## Error semantics

A failure stays a `FieldPathError`, which `EchoColumnState.on_message` already
catches and renders as `?`.

**No new exception type, no new machinery.** That is what keeps three modules
untouched:

- `column_manager.py`
- `echo_column.py`
- `json_column.py` — so `json=true` on an indexed path works for free

One consequence needs stating, because it reads like a bug and is not:

- an out-of-range index shows `?`, and on a detections array **that is the
  normal state, not a config typo**
- `detections[0].id` is `?` on every empty frame
- `detections.#` is `0` at that same moment

*That asymmetry is the point*: **length, not indexing, is what answers the
track-count question.**

## Auto-header sanitizing

Auto-derived headers replace `.` with `_` today, which would produce
`oak_detections[0]_id` and `oak_detections_#`.

Sanitizing extends to the new characters so auto headers stay `[A-Za-z0-9_]`:

- `detections[0].id` → `oak_detections_0_id`
- `detections.#` → `oak_detections_n`

`name=` overrides as always.

## Non-goals

Bias to less code. These stay out until a real config needs one:

- slices (`[1:3]`), wildcards (`[*]`), open-ended or negative-step ranges
- aggregate functions (`min`/`max`/`sum`/`mean`)
- arithmetic, comparisons, filters, or any expression grammar
- `#` anywhere but the final segment

**Length is the single exception**, because a count has no alternative spelling
and every dashboard wants one.

## How to Demo
**Setup**: the `dome_vision` ROS stack running and publishing `/oak/detections`
(`vision_msgs/Detection2DArray`), with at least one object in view.

A conf file containing:

```
sample 2
echo /oak/detections field=detections.#,detections[0].results[0].hypothesis.score name=ntrk,score width=5,6
```

**Steps**:
1. Run `metawtf <that file>`.
2. Watch with objects in view.
3. Cover the camera so the frame goes empty, then uncover it.

**Expected output**: `ntrk` tracks the live detection count and reads `0` on an
empty frame.

`score` shows the first detection's confidence and flips to `?` exactly when the
count hits `0`, recovering when detections return.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
