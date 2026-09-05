#!/usr/bin/env bash
# metawtf installer — assumes ROS2 is already installed and sourced, and
# that the current directory is a colcon workspace root. Clones/updates
# metawtf into ./src, builds it, and prints the one command needed to start
# using it. No Python/colcon knowledge required.
set -euo pipefail

METAWTF_REPO_URL="${METAWTF_REPO_URL:-https://github.com/Boston-Robot-Hackers/metawtf.git}"

check_ros_sourced() {
    if [ -z "${ROS_DISTRO:-}" ]; then
        echo "metawtf install: ROS2 does not look sourced (\$ROS_DISTRO is unset)." >&2
        echo "Run 'source /opt/ros/<distro>/setup.bash' (e.g. jazzy), then re-run this script." >&2
        return 1
    fi
}

check_workspace_dir() {
    local ws="$1"
    if [ ! -d "$ws/src" ]; then
        echo "metawtf install: '$ws' does not look like a colcon workspace (no ./src)." >&2
        echo "cd into your ROS2 workspace root (the directory containing src/), then re-run." >&2
        return 1
    fi
}

os_notice() {
    local os_name="$1"
    if [ "$os_name" != "Linux" ]; then
        echo "metawtf install: this script is only tested on Ubuntu/Linux." >&2
        echo "Continuing on $os_name on a best-effort basis." >&2
    fi
}

clone_or_pull_metawtf() {
    local ws="$1" repo_url="$2"
    local target="$ws/src/metawtf"
    if [ -d "$target" ]; then
        git -C "$target" pull --ff-only
    else
        mkdir -p "$ws/src"
        git clone "$repo_url" "$target"
    fi
}

build_metawtf() {
    local ws="$1"
    (cd "$ws" && colcon build --packages-select metawtf)
}

print_next_steps() {
    local ws="$1"
    cat <<EOF

metawtf built successfully.

Run this once per new shell (or add it to your ~/.bashrc):
    source $ws/install/setup.bash

Then verify with:
    metawtf -h
EOF
}

main() {
    check_ros_sourced || exit 1
    os_notice "$(uname -s)"
    check_workspace_dir "$PWD" || exit 1
    clone_or_pull_metawtf "$PWD" "$METAWTF_REPO_URL"
    build_metawtf "$PWD"
    print_next_steps "$PWD"
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
