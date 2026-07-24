#!/usr/bin/env python3
"""metawtf.cpu_tracker: per-pid CPU% estimation from /proc stat deltas.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import os
import re
from functools import partial
from pathlib import Path

from metawtf.proc_resolve import DEFAULT_PROC_ROOT, resolve_pids
from metawtf.proc_stat import read_total_jiffies


class CpuTracker:
    """Sums CPU% across the pids whose cmdline matches a regex.

    Each sample re-resolves the pid set, so restarts are picked up and
    vanished pids are dropped from the baseline. Per pid with a stored
    baseline it accumulates (Δjiffies / clk_tck) / Δwall × 100 — the psutil
    formula, top's Irix-mode convention where one fully used core is 100%.
    The result is None when no pid had a baseline: a first sighting, or no
    matching process at all.
    """

    def __init__(
        self,
        pattern: re.Pattern,
        proc_root: Path = DEFAULT_PROC_ROOT,
        clk_tck: int | None = None,
        read_jiffies=None,
        own_pid: int | None = None,
    ):
        self.pattern = pattern
        self.proc_root = proc_root
        if clk_tck is None:
            clk_tck = os.sysconf("SC_CLK_TCK")
        self.clk_tck = clk_tck
        self.read_jiffies = read_jiffies or partial(
            read_total_jiffies, proc_root
        )
        if own_pid is None:
            own_pid = os.getpid()
        self.own_pid = own_pid
        self.baselines = {}

    def sample(self, now: float) -> float | None:
        pids = resolve_pids(self.pattern, self.proc_root, self.own_pid)
        next_baselines = {}
        total = 0.0
        has_baseline = False
        for pid in sorted(pids):
            jiffies = self.read_jiffies(pid)
            if jiffies is None:
                continue
            next_baselines[pid] = (jiffies, now)
            previous = self.baselines.get(pid)
            if previous is None:
                continue
            has_baseline = True
            total += self.percent_since(previous, jiffies, now)
        self.baselines = next_baselines
        if not has_baseline:
            return None
        return total

    def percent_since(self, baseline, jiffies: int, now: float) -> float:
        prev_jiffies, prev_time = baseline
        delta_wall = now - prev_time
        if delta_wall <= 0:
            return 0.0
        return ((jiffies - prev_jiffies) / self.clk_tck) / delta_wall * 100.0
