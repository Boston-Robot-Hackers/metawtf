#!/usr/bin/env python3
"""metawtf.sys_cpu_tracker: system-wide CPU% from /proc/stat deltas.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from functools import partial
from pathlib import Path

from metawtf.proc_resolve import DEFAULT_PROC_ROOT
from metawtf.sys_stat import read_system_jiffies


class SysCpuTracker:
    """Reports busy/idle percent of total CPU across all cores.

    Unlike the per-process tracker no wall clock or clk_tck is needed: both
    busy and idle jiffies belong to the same total, so each percent is just
    Δpart / Δtotal × 100 (0-100 across the whole machine, top's Solaris
    mode). The first sample only stores a baseline and reports None.
    """

    def __init__(self, proc_root: Path = DEFAULT_PROC_ROOT, read_jiffies=None):
        self.read_jiffies = read_jiffies or partial(
            read_system_jiffies, proc_root
        )
        self.baseline = None

    def sample(self, now: float) -> tuple[float, float] | None:
        jiffies = self.read_jiffies()
        if jiffies is None:
            self.baseline = None
            return None
        previous, self.baseline = self.baseline, jiffies
        if previous is None:
            return None
        return percents_since(previous, jiffies)


def percents_since(previous, current) -> tuple[float, float] | None:
    prev_busy, prev_idle = previous
    busy, idle = current
    delta_busy = busy - prev_busy
    delta_idle = idle - prev_idle
    delta_total = delta_busy + delta_idle
    if delta_total <= 0:
        return None
    return (
        delta_busy / delta_total * 100.0,
        delta_idle / delta_total * 100.0,
    )
