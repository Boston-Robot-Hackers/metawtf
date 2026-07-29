#!/usr/bin/env python3
"""metawtf.proc_cpu_column: column state for a `proc_cpu` metric.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re

from metawtf.cpu_tracker import CpuTracker


class ProcCpuColumnState:
    """Reports the summed CPU% of the matched process(es) on each tick.

    Unlike the other columns this one has no topic and no subscription — the
    sampler's tick is the only trigger, and all the work happens in the
    tracker against /proc.
    """

    kind = "proc_cpu"

    def __init__(
        self,
        name: str,
        process: re.Pattern,
        width: int | None = None,
        tracker: CpuTracker | None = None,
    ):
        self.name = name
        self.width = width
        self.tracker = tracker or CpuTracker(process)

    def sample(self, now: float) -> str | None:
        percent = self.tracker.sample(now)
        if percent is None:
            return None
        return f"{percent:.1f}%"
