#!/usr/bin/env python3
"""Tests for metawtf.proc_stat.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import pytest

from metawtf.proc_stat import read_total_jiffies, stat_total_jiffies


def stat_line(comm: str, utime: int, stime: int) -> str:
    # Fields after comm: state through cmajflt (11 tokens), then utime, stime.
    return f"1234 ({comm}) S 1 2 3 4 5 6 7 8 9 10 {utime} {stime} 0 0\n"


def test_plain_comm_sums_utime_and_stime():
    assert stat_total_jiffies(stat_line("python3", 10, 5)) == 15


def test_comm_with_spaces_parses():
    assert stat_total_jiffies(stat_line("my proc", 100, 23)) == 123


def test_comm_with_parens_splits_after_last_close():
    assert stat_total_jiffies(stat_line("my (weird) proc", 7, 8)) == 15


def test_comm_with_close_paren_only_splits_after_last():
    assert stat_total_jiffies(stat_line("a)b", 3, 4)) == 7


def test_missing_close_paren_raises():
    with pytest.raises(ValueError, match="no closing paren"):
        stat_total_jiffies("1234 (python3 S 1 2 3")


def test_truncated_line_raises():
    with pytest.raises(ValueError, match="malformed stat line"):
        stat_total_jiffies("1234 (python3) S 1 2")


def test_read_total_jiffies_reads_file(tmp_path):
    pid_dir = tmp_path / "42"
    pid_dir.mkdir()
    (pid_dir / "stat").write_text(stat_line("python3", 11, 12))
    assert read_total_jiffies(tmp_path, 42) == 23


def test_read_total_jiffies_returns_none_when_pid_vanished(tmp_path):
    assert read_total_jiffies(tmp_path, 9999) is None
