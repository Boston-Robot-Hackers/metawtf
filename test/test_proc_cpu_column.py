#!/usr/bin/env python3
"""Tests for metawtf.proc_cpu_column.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import io
import re
from datetime import datetime

from metawtf.proc_cpu_column import ProcCpuColumnState
from metawtf.sampler import Sampler


class FakeTracker:
    def __init__(self, percent):
        self.percent = percent

    def sample(self, now: float):
        return self.percent


def make_column(percent, width: int | None = None) -> ProcCpuColumnState:
    return ProcCpuColumnState(
        "cpu_loop", re.compile("busyloop"), width=width,
        tracker=FakeTracker(percent),
    )


def test_sample_formats_one_decimal_with_percent_sign():
    assert make_column(98.76).sample(0.0) == "98.8%"


def test_sample_is_none_when_tracker_has_no_value():
    assert make_column(None).sample(0.0) is None


def test_row_shows_cpu_value():
    out = io.StringIO()
    sampler = Sampler([make_column(100.0)], out=out)
    sampler.tick(0.0, datetime(2026, 1, 1, 12, 0, 1, 200000))
    lines = out.getvalue().splitlines()
    assert lines[0] == "time, cpu_loop"
    assert lines[1] == "12:00:01.200, 100.0%"


def test_row_cell_is_empty_when_process_absent():
    out = io.StringIO()
    sampler = Sampler([make_column(None)], out=out)
    sampler.tick(0.0, datetime(2026, 1, 1, 12, 0, 1, 200000))
    assert out.getvalue().splitlines()[1] == "12:00:01.200, "


def test_width_pads_cell_like_other_columns():
    out = io.StringIO()
    sampler = Sampler([make_column(100.0, width=8)], out=out)
    sampler.tick(0.0, datetime(2026, 1, 1))
    assert out.getvalue().splitlines()[1] == "00:00:00.000, 100.0%  "
