# TF12 One-command installer for Feature F12

**Date Created:** 2026-09-05

## TF12.0 — `install.sh`: ROS2-sourced check and clear exit

**Status**: done
**Description**: Script checks `$ROS_DISTRO` (or equivalent) is set before
doing anything else; if unset, prints a one-line "source your ROS2
setup.bash, then re-run" message and exits non-zero with no side effects.
Test: extract the check into a small function taking an env-var map (or
reading `$ROS_DISTRO` directly) so it's callable from a bash test harness
with `ROS_DISTRO` unset/set; assert exit code and message.

## TF12.1 — clone-or-pull `metawtf` into the current workspace

**Status**: done
**Description**: Workspace is the current directory (`$PWD`), not a
separate default path. If `src/metawtf` doesn't exist, `git clone`; if it
does, `git pull` instead of failing — safe to re-run. Test: run against a
temp workspace dir with a fake local git remote to verify clone-then-pull
behavior without hitting the network; document if any part (real GitHub
clone) is manual-only.

## TF12.2 — build and verify

**Status**: done (code); live verification pending
**Description**: Runs `colcon build --packages-select metawtf` in the
workspace; on success prints the exact `source .../install/setup.bash` line
and a `metawtf -h` sanity command. Test: this step requires a real ROS2 +
colcon environment, so it's manual-only. Manual test procedure recorded in
`test/test_install.sh`'s header comment (setup, command, expected
observation) — needs to be run on a real ROS2 machine before this feature
can close.

## TF12.3 — non-Linux best-effort notice

**Status**: done
**Description**: Detect `uname` != `Linux`; if so, print a "not officially
tested on this OS" notice before continuing (same logic path, no special
casing beyond the message). Test: unit-test the OS-detection/message
function directly with a mocked `uname` result.

## TF12.4 — README quick start update

**Status**: done
**Description**: README's quick start leads with the one-line installer;
existing manual `colcon build`/`source` steps move under an
"advanced/manual install" heading rather than being deleted. No test (docs
only).

## TF12.5 — test-writing task

**Status**: done
**Description**: Consolidate/finish the bash test harness used by TF12.0,
TF12.1, and TF12.3 (a `test/test_install.sh` or similar, run via plain
`bash`, not pytest); confirm coverage of the ROS2-sourced check, the
clone/pull idempotency logic, and the OS-detection message. Record in the
harness (or a comment) which parts of TF12.2 remain manual-only and why.
`test/test_install.sh` covers all four (8 assertions, run via
`bash test/test_install.sh`); TF12.2's manual procedure is documented in its
header comment.

## TF12.6 — require an existing workspace; error if absent

**Status**: done
**Description**: Script no longer creates a workspace. It requires the
current directory to already look like a colcon workspace root (`./src`
exists) and errors out with a clear message otherwise, before touching
anything else. Test: `check_workspace_dir` unit-tested directly against a
temp dir with and without `./src`.
