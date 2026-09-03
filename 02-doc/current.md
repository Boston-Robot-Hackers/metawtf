# Current Status — Session Handoff

**Last updated:** 2026-09-03

## State

Developing on ROS2 Jazzy (real `rclpy`/`rosidl` available). Full suite:
**262 passed** via plain `python3 -m pytest -q` from the repo root — no `uv`,
no sourced workspace needed. (This file previously said `uv run pytest`/`223
passed`; that was stale — there is no `uv` or `pyproject.toml` in this repo,
per `.claude/settings.json`'s `autoMode.environment` block.)

## Open

**F11 (array indexing and length in field paths): DONE and closed 2026-09-03.**
`field_extract.py` gained `NAME[N]` indexing (negative counts from the end)
and a terminal `NAME.#` length segment; `column_manager.py`, `echo_column.py`,
and `json_column.py` needed no change since they already call `extract_field`
and handle `FieldPathError`. Motivated by `dome_vision`'s I02 load dashboard,
which needed live track count off `/oak/detections` and had no other way to
get it. Live-verified there by Pito 2026-09-03: `ntrk` held steady, dropped to
`0` (a value, not `?`) on an empty frame, and recovered on re-detection.

**F10 (multi-field echo columns): code + tests done, feature file still in
`notdone/`.** `echo TOPIC field=a,b,c` fans one subscription out into one
column per path (parallel to `subfields=` but for real message fields, not
JSON keys). Already in production use by `dome_vision`'s `load.conf`. Move to
`done/` once the live `/cmd_vel` demo (TF10's last task) is run.

**F03 (per-process CPU): code done, TF03.5 (live demo) open.** TF03.0–TF03.4
implemented and tested; the live busyloop demo + colcon check remain.

**Per-kind color grouping landed but was never recorded here.** Human-mode
cells and a grouped kind-header are now colored by column kind; `PinnedHeader`
is ANSI-aware (strips SGR escapes when measuring width so colored, multi-line
headers still wrap correctly). Committed as `de7ad8d`; this file simply never
mentioned it until now.

### ruff has the same undecided policy as `dome_vision`

No ruff config is committed here either, so the effective rule set is
whatever ruff defaults to. Baseline as of this checkpoint: **52 lint findings,
25 files `ruff format` would rewrite**. Dominated by `EXE001
shebang-not-executable`, which directly contradicts `style_guide.md`'s "every
`.py` starts with `#!/usr/bin/env python3`" — the same conflict blocking
`dome_vision`, needing the same decision (disable the rule, or change the
guide) before this can be enforced anywhere.

Two pre-existing findings are worth naming since they sit right next to this
session's `field_extract`/`config.py` edits, but both predate F11 and were
left alone: an unused `keys` local in `config.py:243`, and a duplicate
`test_missing_field_raises` definition in `test/test_config.py` (lines 46 and
284 — the second silently shadows the first).

### `.claude/` kit sync and doc-convention migration landed this checkpoint

A prior session had synced the canonical `.claude/` kit (security hooks —
`block-secrets.sh`, `post-edit-ruff.sh`, `session-start-context.sh` — new
`agents/`, new slash commands, an `autoMode.environment` block) and
retroactively applied the `Date Created` header + `TFNN.N` step-numbering
convention to every `done/` feature and task file, but left all of it
uncommitted across sessions. Verified consistent and complete (spot-checked
F01/TF01) and folded into this checkpoint's commit.

An empty, unexplained `conf/visionwtf.conf` was found alongside it and left
untracked — not part of this commit; ask before deciding what it's for.

The kit brought `.claude/templates/pre-commit.template` (the header-stamping
hook), but it was never materialized: there is no `.githooks/` directory and
`core.hooksPath` is unset, unlike `dome_vision` where the hook is live. No
source file here carries `Version`/`Created`/`Updated` header lines yet. Not
fixed this checkpoint — it's an infrastructure setup task, not a code review
item.

## Open chore

- `colcon test` collects 0 tests though plain `pytest` finds 262; add pytest
  discovery config so the colcon path is green too.

## Parked

- Standalone (non-ROS) install/packaging beyond the `setup.cfg` bin trick —
  revisit only if needed.
