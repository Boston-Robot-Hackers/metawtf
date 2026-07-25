#!/usr/bin/env python3
"""Tests for metawtf.sys_cpu_column.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import io
from datetime import datetime

from metawtf.sampler import Sampler
from metawtf.sys_cpu_column import SysCpuColumnState


class FakeTracker:
    def __init__(self, percents):
        self.percents = percents

    def sample(self, now: float):
        return self.percents


def make_column(mode, percents, width=None) -> SysCpuColumnState:
    return SysCpuColumnState(
        f"cpu_{mode}", mode, width=width, tracker=FakeTracker(percents)
    )


def test_busy_mode_formats_busy_percent():
    assert make_column("busy", (98.76, 1.24)).sample(0.0) == "98.8%"


def test_idle_mode_formats_idle_percent():
    assert make_column("idle", (25.0, 74.94)).sample(0.0) == "74.9%"


def test_sample_is_none_when_tracker_has_no_value():
    assert make_column("busy", None).sample(0.0) is None


def test_row_shows_busy_and_idle_columns():
    out = io.StringIO()
    columns = [make_column("busy", (25.0, 75.0)), make_column("idle", (25.0, 75.0))]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, datetime(2026, 1, 1, 12, 0, 1, 200000))
    lines = out.getvalue().splitlines()
    assert lines[0] == "time, cpu_busy, cpu_idle"
    assert lines[1] == "12:00:01.200, 25.0%, 75.0%"
