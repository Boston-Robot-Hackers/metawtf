# TF11 Array indexing and length in field paths, for Feature F11
**Date Created:** 2026-09-03

All code lands in `metawtf/field_extract.py` (21 lines today) except TF11.3, which
touches `config.py`.

Three modules are deliberately **not** modified — they call `extract_field` and
already handle `FieldPathError`:

- `column_manager.py`
- `echo_column.py`
- `json_column.py`

## TF11.0 — split a path into segments carrying an optional index
**Status**: done
**Description**: Add `parse_path(path) -> list[Segment]` in `field_extract.py`.

A segment is a name plus an optional integer index, so `detections[0].id`
becomes `[(detections, 0), (id, None)]`.

Reject malformed brackets **at parse time**, with `FieldPathError` naming the
offending segment:

- unclosed `[`
- empty `[]`
- non-integer `[a]`
- a stray `]`
- an index on an empty name (`[0].id`)

**Test** in `test/test_field_extract.py`: each well-formed shape parses to the
expected segment list; each malformed shape raises with the segment named.
Parsing is pure, so these are cheap table-driven cases.

## TF11.1 — resolve an index against a sequence
**Status**: done
**Description**: `extract_field` applies a segment's index after the `getattr`.
Negative indices count from the end.

Two distinct failures, both raising `FieldPathError` with the walked-path
context the current code already builds:

- indexing a value that is not a sequence
- an index outside the sequence

**Test**: `detections[0].id` and `detections[-1].id` read the right element on a
populated array; out-of-range raises; indexing a scalar raises; an unindexed
segment on a sequence still returns the sequence itself.

## TF11.2 — terminal `#` length segment
**Status**: done
**Description**: A `#` segment yields `len(value)`.

Legal **only as the final segment**. `detections.#.id` is a `FieldPathError` at
*parse* time, not a walk failure, so the error names the config mistake rather
than a runtime shape.

Rules:

- `#` takes no index — `#[0]` is rejected
- `#` on a value with no `len()` raises `FieldPathError`

**Test**: `detections.#` returns the count; **`0` on an empty array** — the case
that matters, since it must be a value and not `?`; non-final `#` and `#[0]`
raise at parse time; `#` on a scalar raises.

## TF11.3 — auto-header sanitizing for the new characters
**Status**: done
**Description**: `config.subfield_name` replaces only `.` with `_`, so a new
path would auto-name a column `oak_detections[0]_id`.

Extend it to map `[`, `]` and `#` as well, leaving auto headers in
`[A-Za-z0-9_]`:

- `detections[0].id` → `<prefix>_detections_0_id`
- `detections.#` → `<prefix>_detections_n`

No double or trailing underscores. `name=` overrides are untouched.

**Test** in `test/test_config.py`: auto headers for an indexed path, a length
path, and a combined `field=` comma list; an explicit `name=` still wins.

## TF11.4 — end-to-end tests through the column stack
**Status**: done
**Description**: The dedicated test-writing task. The per-step tests above are
unit-level on pure functions; this one proves the untouched modules really are
untouched.

Three cases:

- drive `EchoColumnState.on_message` with a fake message whose array is
  populated, then empty, then populated again — assert the cell goes
  value → `?` → value for an indexed path, and `n` → `0` → `n` for a length path
- one `parse_config` case for the demo conf line in F11, asserting the fan-out
  is one subscription and two named states
- one case through `json_column` on an indexed path, since that is claimed to
  work for free

## TF11.5 — docs
**Status**: done
**Description**: Update the grammar header in `metawtf/metawtf.conf` (the
`field=` rule and the `RULES` block) and `README.md`.

State the `?`-on-empty-array semantics in both — **it is the one behavior a user
will otherwise read as a bug.**

Literate docs are deliberately absent from this list: `process.md` refreshes
them at checkpoint, never as a feature's own task.

## TF11.6 — live demo
**Status**: done

**Command**: `bl dome_vision_ros full_stack.launch.py` (Terminal 1) +
`metawtf ~/ros2_ws/src/dome_vision/dome_vision_ros/config/metawtf/load.conf`
(Terminal 2), against `dome_vision`'s `load.conf`, which carries
`echo /oak/detections field=detections.# name=ntrk width=5`.

**Setup**: OAK-D on USB 3, both packages freshly rebuilt
(`colcon build --packages-select metawtf dome_vision_ros`).

**Expected**: `ntrk` tracks live object count; reads `0` (a value, not `?`) on
an empty frame when the camera is covered; recovers when uncovered.

**Actual (2026-09-03, verified by Pito)**: confirmed correct. Steady state
showed `ntrk` at `3` alongside `tgts` at `2` (one track not yet promoted to a
confirmed target); covering the camera dropped `ntrk` to `0` and it recovered
on uncovering, exactly as designed.
