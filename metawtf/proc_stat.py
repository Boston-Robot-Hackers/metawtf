#!/usr/bin/env python3
"""metawtf.proc_stat: parse /proc/<pid>/stat lines into total jiffies.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from pathlib import Path

# utime and stime are fields 14 and 15 of the stat line; after splitting off
# "pid (comm) " the state field is index 0, so they land at indexes 11 and 12.
UTIME_INDEX = 11
STIME_INDEX = 12


def stat_total_jiffies(stat_line: str) -> int:
    # comm (field 2) may contain spaces or parens, so everything before the
    # LAST ")" is skipped; only the fields after it are positional.
    close = stat_line.rfind(")")
    if close == -1:
        raise ValueError(f"stat line has no closing paren: {stat_line!r}")
    fields = stat_line[close + 1:].split()
    try:
        utime = int(fields[UTIME_INDEX])
        stime = int(fields[STIME_INDEX])
    except (IndexError, ValueError) as error:
        raise ValueError(f"malformed stat line: {stat_line!r}") from error
    return utime + stime


def read_total_jiffies(proc_root: Path, pid: int) -> int | None:
    # None means the process vanished between the /proc scan and this read;
    # a malformed line from a live process raises instead of being guessed at.
    try:
        stat_line = (proc_root / str(pid) / "stat").read_text()
    except OSError:
        return None
    return stat_total_jiffies(stat_line)
