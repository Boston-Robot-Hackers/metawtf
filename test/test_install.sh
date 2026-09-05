#!/usr/bin/env bash
# Unit tests for install.sh's pure logic (check_ros_sourced, os_notice,
# check_workspace_dir, clone_or_pull_metawtf). Plain bash, no framework —
# run directly with `bash test/test_install.sh`.
#
# build_metawtf (TF12.2) is NOT covered here: it requires a real ROS2 +
# colcon environment and is manual-only. Manual test procedure:
#   Setup: a machine with ROS2 sourced, cwd is an existing colcon workspace
#     root (has ./src) without metawtf checked out yet.
#   Command: ./install.sh
#   Expected: clone + colcon build succeed, next-steps message prints the
#     correct `source .../install/setup.bash` line, and `metawtf -h` (after
#     sourcing it) prints help text. Also verify running it from a directory
#     with no ./src prints the workspace error and exits non-zero.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

# shellcheck source=/dev/null
source "$repo_root/install.sh"

failures=0

assert_eq() {
    local desc="$1" expected="$2" actual="$3"
    if [ "$expected" != "$actual" ]; then
        echo "FAIL: $desc (expected '$expected', got '$actual')"
        failures=$((failures + 1))
    else
        echo "PASS: $desc"
    fi
}

assert_status() {
    local desc="$1" expected_status="$2"
    shift 2
    local actual_status=0
    "$@" >/dev/null 2>&1 || actual_status=$?
    assert_eq "$desc" "$expected_status" "$actual_status"
}

# --- check_ros_sourced ---

( unset ROS_DISTRO; assert_status "check_ros_sourced fails when ROS_DISTRO unset" 1 check_ros_sourced )
( export ROS_DISTRO=jazzy; assert_status "check_ros_sourced succeeds when ROS_DISTRO set" 0 check_ros_sourced )

# --- os_notice ---

linux_output="$(os_notice "Linux" 2>&1)"
assert_eq "os_notice is silent on Linux" "" "$linux_output"

mac_output="$(os_notice "Darwin" 2>&1)"
if [[ "$mac_output" == *"best-effort"* ]]; then
    echo "PASS: os_notice warns on non-Linux"
else
    echo "FAIL: os_notice warns on non-Linux (got: $mac_output)"
    failures=$((failures + 1))
fi

# --- check_workspace_dir ---

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

assert_status "check_workspace_dir fails when ./src is absent" 1 check_workspace_dir "$work_dir/not_a_ws"

mkdir -p "$work_dir/real_ws/src"
assert_status "check_workspace_dir succeeds when ./src is present" 0 check_workspace_dir "$work_dir/real_ws"

# --- clone_or_pull_metawtf ---

fake_remote="$work_dir/remote.git"
git init --quiet --bare "$fake_remote"

seed="$work_dir/seed"
git init --quiet "$seed"
git -C "$seed" config user.email "test@example.com"
git -C "$seed" config user.name "Test"
echo "v1" > "$seed/marker.txt"
git -C "$seed" add marker.txt
git -C "$seed" commit --quiet -m "v1"
git -C "$seed" branch -M main
git -C "$seed" remote add origin "$fake_remote"
git -C "$seed" push --quiet -u origin main

ws="$work_dir/real_ws"
clone_or_pull_metawtf "$ws" "$fake_remote"
if [ -f "$ws/src/metawtf/marker.txt" ]; then
    echo "PASS: clone_or_pull_metawtf clones when target absent"
else
    echo "FAIL: clone_or_pull_metawtf clones when target absent"
    failures=$((failures + 1))
fi

echo "v2" > "$seed/marker.txt"
git -C "$seed" commit --quiet -am "v2"
git -C "$seed" push --quiet

clone_or_pull_metawtf "$ws" "$fake_remote"
assert_eq "clone_or_pull_metawtf pulls when target present" "v2" "$(cat "$ws/src/metawtf/marker.txt")"

if [ "$failures" -eq 0 ]; then
    echo "All install.sh tests passed."
    exit 0
else
    echo "$failures test(s) failed."
    exit 1
fi
