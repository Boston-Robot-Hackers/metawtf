#!/usr/bin/env python3
"""Tests for metawtf.sys_cpu_tracker.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from metawtf.sys_cpu_tracker import SysCpuTracker


class FakeReader:
    """A scripted sequence of (busy, idle) jiffies; None means unreadable."""

    def __init__(self, samples):
        self.samples = list(samples)

    def read(self):
        return self.samples.pop(0)

    def tracker(self) -> SysCpuTracker:
        return SysCpuTracker(read_jiffies=self.read)


def test_first_sample_is_none():
    reader = FakeReader([(100, 900)])
    assert reader.tracker().sample(0.0) is None


def test_known_delta_gives_expected_percents():
    reader = FakeReader([(0, 0), (25, 75)])
    tracker = reader.tracker()
    tracker.sample(0.0)
    assert tracker.sample(1.0) == (25.0, 75.0)


def test_percents_sum_to_100_across_cores():
    # 8 jiffies busy + 32 idle over one tick (e.g. 4 cores at clk_tck 10):
    # the pair is a share of the whole machine, never above 100 each.
    reader = FakeReader([(0, 0), (8, 32)])
    tracker = reader.tracker()
    tracker.sample(0.0)
    busy, idle = tracker.sample(1.0)
    assert busy == 20.0
    assert idle == 80.0


def test_zero_delta_returns_none():
    reader = FakeReader([(100, 100), (100, 100)])
    tracker = reader.tracker()
    tracker.sample(0.0)
    assert tracker.sample(1.0) is None


def test_unreadable_stat_resets_baseline():
    reader = FakeReader([(0, 0), None, (50, 50), (60, 60)])
    tracker = reader.tracker()
    tracker.sample(0.0)
    assert tracker.sample(1.0) is None  # unreadable
    assert tracker.sample(2.0) is None  # fresh baseline only
    assert tracker.sample(3.0) == (50.0, 50.0)
