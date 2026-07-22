# Chores

Simple bug fixes and refactors (no spec/behavior change). One line each.

- [x] Resolve `metawtf.yaml` from the current working directory (CLI edit-and-run; reading next to the installed module meant edits needed a `colcon build`). Regression test: `test_config_path_is_current_directory`.
- [x] Echo column default `name` is the sanitized topic when `name` is omitted (was `<topic>_<field>`). Test updated in `test/test_config.py`.
- [x] Bad `field` path shows `?` in that cell instead of crashing the trace; recovers on a later readable message. Tests in `test/test_echo_column.py`.
- [ ] `colcon test --packages-select metawtf` collects 0 tests though plain `pytest` finds all 34; add pytest discovery config (e.g. `testpaths` in `setup.cfg`) so the colcon path is also green.
- [x] Optional per-column `width` field pads each CSV cell (ljust, never truncates) so columns align in the terminal while staying comma-delimited/importable. Threaded config → column states → sampler. Tests in `test/test_sampler.py` and `test/test_config.py`.
- [x] Optional top-level `time:` block with `format` (strftime) and `width`; default keeps `HH:MM:SS.mmm`. Tests in `test/test_config.py` and `test/test_sampler.py`.
- [x] Graceful exit: press bare `q` (cbreak mode, no Enter) or Ctrl-C; clean shutdown with no traceback. Falls back to Ctrl-C only when stdin is not a tty. `wait_for_quit` unit-tested in `test/test_tracer_node.py`.
- [x] Make `metawtf` a byproduct of `colcon build`: `setup.cfg` installs the console script to `$base/bin` (not `lib/metawtf`), so `metawtf` lands on PATH after `colcon build` + `source install/setup.bash`. Trade-off: `ros2 run metawtf metawtf` no longer resolves it (invoke as `metawtf`).
