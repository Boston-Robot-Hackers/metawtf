#!/usr/bin/env python3
"""metawtf.sys_cpu_column: column state for a `sys_cpu` metric.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from metawtf.sys_cpu_tracker import SysCpuTracker

BUSY = "busy"
IDLE = "idle"


class SysCpuColumnState:
    """Reports the system-wide busy or idle CPU% on each tick.

    Like proc_cpu there is no topic and no subscription — the sampler's tick
    is the only trigger. `mode` selects which half of the tracker's
    (busy, idle) pair this column renders.
    """

    kind = "sys_cpu"

    def __init__(
        self,
        name: str,
        mode: str,
        width: int | None = None,
        tracker: SysCpuTracker | None = None,
    ):
        self.name = name
        self.mode = mode
        self.width = width
        self.tracker = tracker or SysCpuTracker()

    def sample(self, now: float) -> str | None:
        percents = self.tracker.sample(now)
        if percents is None:
            return None
        busy, idle = percents
        value = busy if self.mode == BUSY else idle
        return f"{value:.1f}%"
