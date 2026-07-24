#!/usr/bin/env python3
"""Tests for metawtf.cpu_tracker.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re
import shutil

from metawtf.cpu_tracker import CpuTracker

CLK_TCK = 100


class FakeProc:
    """A tmpdir /proc tree plus a fake jiffies reader over the same pids."""

    def __init__(self, proc_root):
        self.proc_root = proc_root
        self.jiffies = {}

    def add(self, pid: int, jiffies: int) -> None:
        pid_dir = self.proc_root / str(pid)
        pid_dir.mkdir(exist_ok=True)
        (pid_dir / "cmdline").write_bytes(b"busyloop\x00")
        self.jiffies[pid] = jiffies

    def set_jiffies(self, pid: int, jiffies: int) -> None:
        self.jiffies[pid] = jiffies

    def remove(self, pid: int) -> None:
        shutil.rmtree(self.proc_root / str(pid))
        del self.jiffies[pid]

    def read(self, pid: int) -> int | None:
        return self.jiffies.get(pid)

    def tracker(self) -> CpuTracker:
        return CpuTracker(
            re.compile("busyloop"),
            proc_root=self.proc_root,
            clk_tck=CLK_TCK,
            read_jiffies=self.read,
        )


def test_first_sample_is_none(tmp_path):
    proc = FakeProc(tmp_path)
    proc.add(100, 1000)
    assert proc.tracker().sample(0.0) is None


def test_no_matching_process_is_none(tmp_path):
    proc = FakeProc(tmp_path)
    assert proc.tracker().sample(0.0) is None


def test_known_delta_gives_expected_percent(tmp_path):
    proc = FakeProc(tmp_path)
    proc.add(100, 1000)
    tracker = proc.tracker()
    tracker.sample(0.0)
    proc.set_jiffies(100, 1100)  # 100 jiffies = 1.0s of CPU over 1.0s wall
    assert tracker.sample(1.0) == 100.0


def test_percent_can_exceed_100_for_multi_core_work(tmp_path):
    proc = FakeProc(tmp_path)
    proc.add(100, 0)
    tracker = proc.tracker()
    tracker.sample(0.0)
    proc.set_jiffies(100, 250)  # 2.5 cores over 1.0s wall
    assert tracker.sample(1.0) == 250.0


def test_two_matching_pids_are_summed(tmp_path):
    proc = FakeProc(tmp_path)
    proc.add(100, 0)
    proc.add(200, 0)
    tracker = proc.tracker()
    tracker.sample(0.0)
    proc.set_jiffies(100, 100)
    proc.set_jiffies(200, 50)
    assert tracker.sample(1.0) == 150.0


def test_vanished_pid_is_dropped_from_baseline(tmp_path):
    proc = FakeProc(tmp_path)
    proc.add(100, 0)
    proc.add(200, 0)
    tracker = proc.tracker()
    tracker.sample(0.0)
    proc.remove(200)
    proc.set_jiffies(100, 100)
    assert tracker.sample(1.0) == 100.0
    assert set(tracker.baselines) == {100}


def test_last_pid_vanishing_returns_none(tmp_path):
    proc = FakeProc(tmp_path)
    proc.add(100, 0)
    tracker = proc.tracker()
    tracker.sample(0.0)
    proc.remove(100)
    assert tracker.sample(1.0) is None


def test_restarted_process_is_picked_up_with_fresh_baseline(tmp_path):
    proc = FakeProc(tmp_path)
    proc.add(100, 0)
    tracker = proc.tracker()
    tracker.sample(0.0)
    proc.remove(100)
    tracker.sample(1.0)
    proc.add(300, 5000)
    assert tracker.sample(2.0) is None  # new pid: first sighting
    proc.set_jiffies(300, 5100)
    assert tracker.sample(3.0) == 100.0
