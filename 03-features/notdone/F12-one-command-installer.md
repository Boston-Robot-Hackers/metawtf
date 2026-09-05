# F12 — one-command installer for non-technical users

**Priority**: Medium
**Date Created:** 2026-09-05
**Done:** no
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Note:** code + `test/test_install.sh` (8 assertions) complete for TF12.0,
TF12.1, TF12.3, TF12.4, TF12.6. TF12.2 (the actual `colcon build` step) needs
a real ROS2 machine to verify live — see "How to Demo" — before this can move
to `done/`.
**Description**: A single `install.sh` script that lets someone with no
Python, `colcon`, or ROS2-packaging knowledge get `metawtf` running with one
command.

**Assumption**: the target machine already has ROS2 (Jazzy or compatible)
installed and sourced — this feature does not install ROS2 itself, only
`metawtf` on top of it.

The script:

- Detects whether ROS2 is sourced (`$ROS_DISTRO`); if not, prints a clear
  "source your ROS2 setup.bash first" message and exits — no partial state.
- Requires the current directory to already be a colcon workspace root (has
  `./src`); errors out with a clear message rather than creating one.
- Clones `metawtf` into `./src` if absent, or `git pull`s it if already
  present (safe to re-run).
- Runs `colcon build --packages-select metawtf`.
- Prints the one line to source (`source install/setup.bash`) and a command
  to verify success (`metawtf -h`).

**Platform scope**: Ubuntu is the primary, tested target. macOS and Windows
are best-effort — the script runs the same logic there (ROS2-on-non-Linux
setups still use `colcon`) and prints a "not officially tested on this OS"
notice, but no dedicated non-Linux testing or troubleshooting is in scope for
this feature.

README's quick start gets updated to lead with this one-liner, moving the
manual `colcon build`/`source` steps to an "advanced/manual install" section
rather than removing them.

## How to Demo

**Setup**: a fresh Ubuntu machine with ROS2 Jazzy installed and sourced, and
an existing colcon workspace (`~/ros2_ws` with a `src/` directory) that does
not yet contain `metawtf`.

**Steps**:
1. `cd ~/ros2_ws`.
2. Run the installer (e.g. `curl -sSL <repo raw url>/install.sh | bash`, or
   download and run `./install.sh` locally).
3. Follow the one printed instruction (source `install/setup.bash`, unless
   already sourced by the current shell).
4. Run `metawtf -h`.
5. Separately, confirm running the installer from a directory with no
   `src/` prints the workspace error and exits non-zero instead of creating
   one.

**Expected output**: help text prints. At no point does the user need to
know what `pip`, `colcon`, or a Python package even are.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code or content until the
user gives explicit approval to proceed.
