#!/usr/bin/env python3
"""Tests for metawtf.sampler.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import io
from datetime import datetime

from metawtf.sampler import Sampler


class FakeColumn:
    def __init__(self, name: str, value):
        self.name = name
        self.value = value

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
