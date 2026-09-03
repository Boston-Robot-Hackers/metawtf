# TF09 — Clear the screen when the pinned header first appears (Feature F09)
**Date Created:** 2026-07-25

## TF09.0 — Clear the screen in PinnedHeader.setup
**Status**: done
**Description**: In `metawtf/terminal.py`, `PinnedHeader.setup` emits a
clear-screen (`CSI 2J`) before homing the cursor and drawing the header, so the
first pinned header starts on a clean screen. `draw_header` (in-place redraw)
is unchanged. Update the exact-string `test_setup_*` assertions in
`test/test_terminal.py` to include the clear and add/confirm a test that the
clear precedes the header. Run the full suite.
