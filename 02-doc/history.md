# Project History

Completed features, resolved issues, and other closed-out context, moved
here from `02-doc/current.md` once no longer "current." Newest first.

## 2026-09-07

**F13 (Buddy's display requests): closed.** Three bundled requests: (1) the
pinned header now re-pins on any terminal resize, not only when a column is
added — a poll-based per-tick size check in `Sampler.tick` (not `SIGWINCH`:
simpler, portable, and consistent with the codebase's existing poll-driven
header-growth check); (2) `width=N%` is now accepted everywhere `width=N`
is, resolved against the live terminal width at render time (`PercentWidth`
in `config.py`, `resolve_width()` in `sampler.py`), coexisting with fixed
widths including within one multi-field comma list; (3) README now states
that `proc_cpu`/`sys_cpu` require `metawtf` to run on the same machine as
the measured ROS2 node(s), since both read local `/proc`. 14 new tests
across `test_config.py`/`test_sampler.py`; full suite 244 passed, 4 skipped
on this (no-ROS2) machine, same known `rosidl_runtime_py` gap unaffected.

**`conf/load-thermal-survey.conf` added.** A real-world example config
(adapted from `dome_vision`'s `dome_vision_ros/config/metawtf/load.conf`,
given a clearer name) combining multi-field `echo`, `hz`, `sys_cpu`, and
`proc_cpu` to diagnose an undervoltage reset — a useful complement to
`conf/metawtf.conf`'s syntax-coverage example. Referenced in README's
Examples section; logged as a chore (doc-only, no spec change).

**`.claude/` re-synced from the canonical `j3` kit.** `process.md`,
`style_guide.md`, `literate.md`, `bootstrap.md`, `agents/`, `hooks/`, and
most `templates/` were already identical — j3 had caught up since an
earlier comparison this session found it drifted toward an unrelated
`oak_roboflow` project's customizations. Copied three genuinely-improved
command files from j3: `commands/checkpoint.md`, `commands/feature.md`
(now points at the canonical `.claude/templates/feature-template.md`/
`task_template.md` instead of metawtf's own stale root-level duplicates —
see the new chore in `current.md`), and `commands/start.md`. Deliberately
did **not** copy `settings.json` (metawtf's has real project values; j3's
is still the generic bootstrap placeholder) or `settings.local.json`
(gitignored/machine-local, per `process.md`'s own rule). j3's
`templates/CLAUDE.md.template` still has unresolved git merge-conflict
markers (`<<<<<<< HEAD`/`=======`/`>>>>>>>`) — flagged to the user, not
copied.

## 2026-09-05

**`TimeColumn` crash on `--color` fixed.** A user on a real ROS2/colcon
workspace hit `AttributeError: 'TimeColumn' object has no attribute 'name'`
on every plain `metawtf` run — color defaults on whenever stdout is a real
terminal in human mode (`tracer_node.py`'s `color=self.pinned is not None`),
and `join_group_header`'s width fallback needed `col.name`, which `TimeColumn`
never had. This is the exact path the README's own quick-start example takes.
Fixed by adding `name: str = "time"` to `TimeColumn` (`config.py`); logged as
a chore in `04-tasks/chores.md` with regression test
`test_color_group_header_with_default_time_column`
(`test/test_sampler.py`). Verified end-to-end by parsing the README's exact
quick-start config through `parse_config` → `Sampler(..., color=True)`:
pre-fix reproduced the identical traceback, post-fix renders cleanly.
Committed as `3e632bd`. Not yet reconfirmed on the reporting user's own
machine.

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
