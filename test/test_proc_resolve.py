#!/usr/bin/env python3
"""Tests for metawtf.proc_resolve.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re

from metawtf.proc_resolve import resolve_pids


def add_process(proc_root, pid: int, cmdline: bytes) -> None:
    pid_dir = proc_root / str(pid)
    pid_dir.mkdir()
    (pid_dir / "cmdline").write_bytes(cmdline)


def test_matching_python_style_cmdline_is_found(tmp_path):
    add_process(tmp_path, 100, b"python3\x00/opt/ros/bin/controller_server\x00")
    pattern = re.compile("controller_server")
    assert resolve_pids(pattern, tmp_path) == {100}


def test_non_matching_entry_is_skipped(tmp_path):
    add_process(tmp_path, 100, b"python3\x00controller_server\x00")
    add_process(tmp_path, 101, b"bash\x00")
    pattern = re.compile("controller_server")
    assert resolve_pids(pattern, tmp_path) == {100}


def test_empty_cmdline_is_skipped(tmp_path):
    add_process(tmp_path, 100, b"")
    pattern = re.compile(".")
    assert resolve_pids(pattern, tmp_path) == set()


def test_own_pid_is_excluded(tmp_path):
    add_process(tmp_path, 100, b"python3\x00controller_server\x00")
    pattern = re.compile("controller_server")
    assert resolve_pids(pattern, tmp_path, own_pid=100) == set()


def test_unreadable_cmdline_is_skipped(tmp_path):
    pid_dir = tmp_path / "100"
    pid_dir.mkdir()
    (pid_dir / "cmdline").mkdir()  # reading a directory raises OSError
    pattern = re.compile(".")
    assert resolve_pids(pattern, tmp_path) == set()


def test_non_numeric_entries_are_ignored(tmp_path):
    add_process(tmp_path, 100, b"busyloop\x00")
    (tmp_path / "bus").mkdir()
    (tmp_path / "version").write_text("busyloop")
    pattern = re.compile("busyloop")
    assert resolve_pids(pattern, tmp_path) == {100}


def test_multiple_matches_all_returned(tmp_path):
    add_process(tmp_path, 100, b"python3\x00controller_server\x00")
    add_process(tmp_path, 200, b"controller_server\x00--ros-args\x00")
    pattern = re.compile("controller_server")
    assert resolve_pids(pattern, tmp_path) == {100, 200}
