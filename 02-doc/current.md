# Current Status — Session Handoff

**Last updated:** 2026-09-07

## State

Developing on ROS2 Jazzy (real `rclpy`/`rosidl` available). On this Mac (no
ROS2 install): **244 passed, 4 skipped, 10 failed** via plain
`python3 -m pytest -q` from the repo root — the 10 failures are the known
`rosidl_runtime_py` gap below, not a regression. Last confirmed clean run on
a ROS2-sourced machine was **262 passed** (pre-F13); not yet reconfirmed
there with F13's 14 new tests, so expect ~276 passed on that machine but
treat it as unverified until actually run.

**Correction to the "no sourced workspace needed" claim above:** it does not
hold on a machine with no ROS2 install at all. `metawtf/msg_type.py` imports
`rosidl_runtime_py` (a dependency since the original TF01 commit), so
`test/test_column_manager.py`'s 10 tests fail to collect without ROS2
sourced. Not a regression — just know which machine you're on.

## Open

**F03 (per-process CPU): code done, TF03.5 (live demo) open.** TF03.0–TF03.4
implemented and tested; the live busyloop demo + colcon check remain.

**F12 (one-command installer): code + tests done, live verification open.**
New `install.sh` at repo root, run from inside an existing colcon workspace
(the directory containing `src/`): checks `$ROS_DISTRO` is set, requires
`./src` to already exist (errors out rather than creating a workspace),
clones or `git pull`s `metawtf` into `./src`, runs
`colcon build --packages-select metawtf`, prints the `source
install/setup.bash` line. Non-Linux gets a best-effort notice, same code
path. README's Installation section leads with the one-liner; the old
manual steps moved to a "Manual install" subsection. `test/test_install.sh`
(plain bash, 8 assertions) covers the ROS2-check, workspace-check,
OS-notice, and clone/pull-idempotency logic against a local fake git remote.
Not yet closed: TF12.2 (the actual `colcon build`, from inside a real
workspace) needs to be run on a real ROS2 machine before `done/`.

### ruff has the same undecided policy as `dome_vision`

No ruff config is committed here either, so `ruff check .` runs on
whatever ruff's bare defaults are — currently **5 E402 findings**, all in
`test/test_tracer_node.py`, where imports come after the `rclpy =
pytest.importorskip("rclpy")` line by necessity (that line must run first to
skip the whole file cleanly when `rclpy` is absent) — a justified violation,
not an oversight; see the matching entry in `04-tasks/chores.md`.
`ruff format --check .` would rewrite **15 files** (up from 14 previously
noted — some touched by F13), all line-wrapping/list-formatting choices
unrelated to any current work's actual logic. The underlying open question
is unchanged: no decision has been made on adopting `ruff format`/a wider
rule set repo-wide, same as `dome_vision`.

The kit's `.claude/templates/pre-commit.template` (the header-stamping hook)
is still not materialized: no `.githooks/` directory, `core.hooksPath`
unset. No source file here carries `Version`/`Created`/`Updated` header
lines yet.

## Open chore

- `colcon test` collects 0 tests though plain `pytest` finds 262; add pytest
  discovery config so the colcon path is green too.
- `03-features/template.md` and `04-tasks/template.md` are stale duplicates
  of `.claude/templates/feature-template.md`/`task_template.md` (missing
  `Date Created:`; old `T01`/`T02` step numbering instead of `TFNN.N`).
  `.claude/commands/feature.md` was just repointed at the canonical
  `.claude/templates/` pair (this session's `.claude` sync from `j3`), but
  the stale root-level copies are still there — delete or refresh them.

## Parked

- Standalone (non-ROS) install/packaging beyond the `setup.cfg` bin trick —
  revisit only if needed. (F12 doesn't replace this: it still assumes ROS2
  and a colcon workspace are already present.)

## History

Closed features and resolved items are in `02-doc/history.md`, not appended
here.
