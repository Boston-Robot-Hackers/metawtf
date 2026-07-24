#!/usr/bin/env python3
"""metawtf.sys_stat: parse the aggregate cpu line of /proc/stat.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from pathlib import Path

# Fields of the aggregate "cpu" line, in order. Busy counts work; idle counts
# waiting (idle plus iowait, the usual top/htop convention). guest/guest_nice
# are already included in user/nice, so they are never added separately.
BUSY_FIELDS = ("user", "nice", "system", "irq", "softirq", "steal")
IDLE_FIELDS = ("idle", "iowait")
ALL_FIELDS = BUSY_FIELDS[:3] + IDLE_FIELDS + BUSY_FIELDS[3:]


def system_jiffies(stat_text: str) -> tuple[int, int]:
    """Return (busy, idle) jiffies from the aggregate cpu line."""
    first_line = stat_text.split("\n", 1)[0]
    fields = first_line.split()
    if not fields or fields[0] != "cpu":
        raise ValueError(f"no aggregate cpu line: {first_line!r}")
    try:
        values = [int(field) for field in fields[1:]]
    except ValueError as error:
        raise ValueError(f"malformed cpu line: {first_line!r}") from error
    # Older kernels report fewer fields; the missing ones contribute zero.
    values += [0] * (len(ALL_FIELDS) - len(values))
    jiffies = dict(zip(ALL_FIELDS, values))
    busy = sum(jiffies[name] for name in BUSY_FIELDS)
    idle = sum(jiffies[name] for name in IDLE_FIELDS)
    return busy, idle


def read_system_jiffies(proc_root: Path) -> tuple[int, int] | None:
    # None means the stat file could not be read at all; a malformed line
    # raises instead of being guessed at.
    try:
        stat_text = (proc_root / "stat").read_text()
    except OSError:
        return None
    return system_jiffies(stat_text)
