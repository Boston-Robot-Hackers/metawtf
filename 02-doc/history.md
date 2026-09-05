# Project History

Completed features, resolved issues, and other closed-out context, moved
here from `02-doc/current.md` once no longer "current." Newest first.

## 2026-09-05

**F10 (multi-field echo columns): closed.** `echo TOPIC field=a,b,c` fans
one subscription out into one column per path (parallel to `subfields=` but
for real message fields, not JSON keys). Already in production use by
`dome_vision`'s `load.conf`. Live `/cmd_vel` demo verified by Pito: two
columns tracked correctly from one subscription; full suite (262 passed)
confirmed clean on a ROS2-equipped machine.

**Two lint findings fixed as chores.** An unused `keys` local in
`config.py`'s `parse_echo_column`, and a duplicate `test_missing_field_raises`
definition in `test/test_config.py` (the second silently shadowing the
first, since renamed to `test_missing_field_raises_with_field_message` so
both cases run). See `04-tasks/chores.md`.

**Empty, untracked `conf/visionwtf.conf` resolved.** Deleted by Pito; no
longer an open question.

## 2026-09-03

**README.md rewritten** as an open-source-project README (tagline,
sample-output preview, comparison against `ros2 topic echo`/`rqt`/Foxglove/
`ros2 bag`, key features, requirements, quick start, full configuration
reference, examples, troubleshooting) rather than the old grammar-reference-only
version. Internals/theory-of-operation are pointed at `01-literate/`, not
inlined, per the project's own convention that the README stays "how to use
this," not "how it works inside."

**F11 (array indexing and length in field paths): closed.**
`field_extract.py` gained `NAME[N]` indexing (negative counts from the end)
and a terminal `NAME.#` length segment; `column_manager.py`, `echo_column.py`,
and `json_column.py` needed no change since they already call `extract_field`
and handle `FieldPathError`. Motivated by `dome_vision`'s I02 load dashboard,
which needed live track count off `/oak/detections` and had no other way to
get it. Live-verified there by Pito: `ntrk` held steady, dropped to `0` (a
value, not `?`) on an empty frame, and recovered on re-detection.

**`.claude/` kit sync and doc-convention migration landed.** A prior session
had synced the canonical `.claude/` kit (security hooks —
`block-secrets.sh`, `post-edit-ruff.sh`, `session-start-context.sh` — new
`agents/`, new slash commands, an `autoMode.environment` block) and
retroactively applied the `Date Created` header + `TFNN.N` step-numbering
convention to every `done/` feature and task file, but left all of it
uncommitted across sessions. Verified consistent and complete (spot-checked
F01/TF01) and folded into that checkpoint's commit.

The kit brought `.claude/templates/pre-commit.template` (the header-stamping
hook), but it was never materialized: there is no `.githooks/` directory and
`core.hooksPath` is unset, unlike `dome_vision` where the hook is live. No
source file here carries `Version`/`Created`/`Updated` header lines yet —
still an open infrastructure gap, not resolved by this migration.

## (undated, recorded retroactively)

**Per-kind color grouping.** Human-mode cells and a grouped kind-header are
colored by column kind; `PinnedHeader` is ANSI-aware (strips SGR escapes when
measuring width so colored, multi-line headers still wrap correctly).
Committed as `de7ad8d`.
