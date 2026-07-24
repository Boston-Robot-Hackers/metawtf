#!/usr/bin/env python3
"""metawtf.proc_resolve: find pids whose cmdline matches a regex.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re
from pathlib import Path

DEFAULT_PROC_ROOT = Path("/proc")


def resolve_pids(
    pattern: re.Pattern,
    proc_root: Path = DEFAULT_PROC_ROOT,
    own_pid: int | None = None,
) -> set[int]:
    pids = set()
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == own_pid:
            continue
        cmdline = read_cmdline(entry)
        if cmdline is not None and pattern.search(cmdline):
            pids.add(pid)
    return pids


def read_cmdline(pid_dir: Path) -> str | None:
    # Matching is against the full argv (NUL-separated args joined with
    # spaces), not comm: Python ROS nodes all have comm "python3". Kernel
    # threads have an empty cmdline, and an unreadable one means the process
    # vanished mid-scan or belongs to another user — both are skips, not
    # errors.
    try:
        raw = (pid_dir / "cmdline").read_bytes()
    except OSError:
        return None
    args = [arg for arg in raw.decode(errors="replace").split("\0") if arg]
    if not args:
        return None
    return " ".join(args)
