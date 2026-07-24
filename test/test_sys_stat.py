#!/usr/bin/env python3
"""Tests for metawtf.sys_stat.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import pytest

from metawtf.sys_stat import read_system_jiffies, system_jiffies

# user nice system idle iowait irq softirq steal
STAT_LINE = "cpu  100 0 50 800 20 10 5 15 0 0\n"


def test_parses_busy_and_idle_jiffies():
    busy, idle = system_jiffies(STAT_LINE + "cpu0 1 2 3 4 5 6 7 8\n")
    assert busy == 100 + 0 + 50 + 10 + 5 + 15  # user+nice+system+irq+softirq+steal
    assert idle == 800 + 20  # idle + iowait


def test_missing_fields_count_as_zero():
    # Old kernels stop after iowait (or earlier); absent fields contribute 0.
    busy, idle = system_jiffies("cpu 100 0 50 800\n")
    assert busy == 150
    assert idle == 800


def test_guest_fields_are_not_double_counted():
    # guest/guest_nice are already inside user/nice; adding them would inflate.
    busy, _idle = system_jiffies("cpu 100 0 50 800 20 10 5 15 999 888\n")
    assert busy == 180


def test_line_without_cpu_prefix_raises():
    with pytest.raises(ValueError):
        system_jiffies("proc 100 0 50 800\n")


def test_non_numeric_field_raises():
    with pytest.raises(ValueError):
        system_jiffies("cpu 100 x 50 800\n")


def test_read_returns_none_when_stat_missing(tmp_path):
    assert read_system_jiffies(tmp_path) is None


def test_read_parses_stat_file(tmp_path):
    (tmp_path / "stat").write_text(STAT_LINE)
    assert read_system_jiffies(tmp_path) == (180, 820)
