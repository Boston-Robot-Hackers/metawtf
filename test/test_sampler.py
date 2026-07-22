#!/usr/bin/env python3
"""Tests for metawtf.sampler.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import io
from datetime import datetime

from metawtf.config import TimeColumn
from metawtf.sampler import Sampler


class FakeColumn:
    def __init__(self, name: str, value, width: int | None = None):
        self.name = name
        self.value = value
        self.width = width

    def sample(self, now: float):
        return self.value


def test_header_and_row_format():
    out = io.StringIO()
    columns = [FakeColumn("odom_x", "1.5"), FakeColumn("odom_z", None)]
    sampler = Sampler(columns, out=out)
    wall = datetime(2026, 1, 1, 12, 0, 1, 200000)
    sampler.tick(now_monotonic=0.0, now_wall=wall)
    lines = out.getvalue().splitlines()
    assert lines[0] == "time,odom_x,odom_z"
    assert lines[1] == "12:00:01.200,1.5,"


def test_header_only_printed_once():
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out)
    wall = datetime(2026, 1, 1, 0, 0, 0)
    sampler.tick(0.0, wall)
    sampler.tick(1.0, wall)
    lines = out.getvalue().splitlines()
    assert lines.count("time,a") == 1
    assert len(lines) == 3


def test_width_pads_header_and_cells_but_keeps_commas():
    out = io.StringIO()
    columns = [FakeColumn("cpu", "1.5", width=8), FakeColumn("odom_z", None)]
    sampler = Sampler(columns, out=out)
    wall = datetime(2026, 1, 1, 12, 0, 1, 200000)
    sampler.tick(now_monotonic=0.0, now_wall=wall)
    lines = out.getvalue().splitlines()
    assert lines[0] == "time,cpu,     odom_z"
    assert lines[1] == "12:00:01.200,1.5,     "


def test_time_format_and_width_applied():
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    time = TimeColumn(format="%H:%M:%S", width=10)
    sampler = Sampler(columns, time=time, out=out)
    wall = datetime(2026, 1, 1, 12, 0, 1, 200000)
    sampler.tick(now_monotonic=0.0, now_wall=wall)
    lines = out.getvalue().splitlines()
    assert lines[0] == "time,      a"
    assert lines[1] == "12:00:01,  1"


def test_default_time_keeps_millisecond_format():
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out)
    wall = datetime(2026, 1, 1, 12, 0, 1, 200000)
    sampler.tick(now_monotonic=0.0, now_wall=wall)
    assert out.getvalue().splitlines()[1] == "12:00:01.200,1"


def test_width_does_not_truncate_longer_values():
    out = io.StringIO()
    columns = [FakeColumn("cpu", "123456789", width=4)]
    sampler = Sampler(columns, out=out)
    wall = datetime(2026, 1, 1, 0, 0, 0)
    sampler.tick(0.0, wall)
    assert out.getvalue().splitlines()[1] == "00:00:00.000,123456789"


def test_header_reprinted_when_column_added():
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out)
    wall = datetime(2026, 1, 1, 0, 0, 0)
    sampler.tick(0.0, wall)
    columns.append(FakeColumn("b", "2"))
    sampler.tick(1.0, wall)
    sampler.tick(2.0, wall)
    lines = out.getvalue().splitlines()
    assert lines == [
        "time,a",
        "00:00:00.000,1",
        "time,a,b",
        "00:00:00.000,1,2",
        "00:00:00.000,1,2",
    ]
