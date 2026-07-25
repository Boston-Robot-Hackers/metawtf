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


WALL = datetime(2026, 1, 1, 12, 0, 1, 200000)
MIDNIGHT = datetime(2026, 1, 1)


def test_human_header_and_row_format():
    out = io.StringIO()
    columns = [FakeColumn("odom_x", "1.5"), FakeColumn("odom_z", None)]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(now_monotonic=0.0, now_wall=WALL)
    lines = out.getvalue().splitlines()
    assert lines[0] == "time, odom_x, odom_z"
    assert lines[1] == "12:00:01.200, 1.5, "


def test_header_only_printed_once():
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, MIDNIGHT)
    sampler.tick(1.0, MIDNIGHT)
    lines = out.getvalue().splitlines()
    assert lines.count("time, a") == 1
    assert len(lines) == 3


def test_width_pads_header_and_cells_but_keeps_commas():
    out = io.StringIO()
    columns = [FakeColumn("cpu", "1.5", width=8), FakeColumn("odom_z", None)]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(now_monotonic=0.0, now_wall=WALL)
    lines = out.getvalue().splitlines()
    assert lines[0] == "time, cpu,      odom_z"
    assert lines[1] == "12:00:01.200, 1.5,      "


def test_time_format_and_width_applied():
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    time = TimeColumn(format="%H:%M:%S", width=10)
    sampler = Sampler(columns, time=time, out=out, human=True)
    sampler.tick(now_monotonic=0.0, now_wall=WALL)
    lines = out.getvalue().splitlines()
    assert lines[0] == "time,       a"
    assert lines[1] == "12:00:01,   1"


def test_default_time_keeps_millisecond_format():
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(now_monotonic=0.0, now_wall=WALL)
    assert out.getvalue().splitlines()[1] == "12:00:01.200, 1"


def test_column_widens_to_fit_long_header():
    # cpu_nav2 (8 chars) in a width-6 column: without widening the header
    # overflows and its later cells drift right of the data rows.
    out = io.StringIO()
    columns = [
        FakeColumn("cpu_nav2", "100.0%", width=6),
        FakeColumn("hz", "20.00", width=6),
    ]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, MIDNIGHT)
    lines = out.getvalue().splitlines()
    assert lines[0] == "time, cpu_nav2, hz    "
    assert lines[1] == "00:00:00.000, 100.0%,   20.00 "


def test_human_truncates_long_value_with_ellipsis():
    out = io.StringIO()
    columns = [FakeColumn("cpu", "123456789", width=4)]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[1] == "00:00:00.000, 123…"


def test_truncated_value_keeps_later_cells_aligned():
    out = io.StringIO()
    columns = [
        FakeColumn("cpu", "123456789", width=4),
        FakeColumn("x", "1"),
    ]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[1] == "00:00:00.000, 123…, 1"


def test_human_does_not_truncate_without_width():
    out = io.StringIO()
    columns = [FakeColumn("note", "a very long value indeed")]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[1] == "00:00:00.000, a very long value indeed"


def test_human_does_not_quote_values():
    out = io.StringIO()
    columns = [FakeColumn("note", "a,b"), FakeColumn("x", "1")]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[1] == "00:00:00.000, a,b, 1"


def test_on_header_intercepts_the_header_print():
    out = io.StringIO()
    headers = []
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out, human=True, on_header=headers.append)
    sampler.tick(0.0, MIDNIGHT)
    assert headers == ["time, a"]
    assert out.getvalue().splitlines() == ["00:00:00.000, 1"]


def test_header_reprinted_when_column_added():
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, MIDNIGHT)
    columns.append(FakeColumn("b", "2"))
    sampler.tick(1.0, MIDNIGHT)
    sampler.tick(2.0, MIDNIGHT)
    lines = out.getvalue().splitlines()
    assert lines == [
        "time, a",
        "00:00:00.000, 1",
        "time, a, b",
        "00:00:00.000, 1, 2",
        "00:00:00.000, 1, 2",
    ]


def test_csv_header_and_row_have_no_padding():
    out = io.StringIO()
    columns = [FakeColumn("odom_x", "1.5"), FakeColumn("odom_z", None)]
    sampler = Sampler(columns, out=out, human=False)
    sampler.tick(now_monotonic=0.0, now_wall=WALL)
    lines = out.getvalue().splitlines()
    assert lines[0] == "time,odom_x,odom_z"
    assert lines[1] == "12:00:01.200,1.5,"


def test_csv_ignores_width_and_keeps_full_values():
    out = io.StringIO()
    columns = [FakeColumn("cpu", "123456789", width=4)]
    sampler = Sampler(columns, out=out, human=False)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[1] == "00:00:00.000,123456789"


def test_csv_header_reprinted_when_column_added():
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out, human=False)
    sampler.tick(0.0, MIDNIGHT)
    columns.append(FakeColumn("b", "2"))
    sampler.tick(1.0, MIDNIGHT)
    lines = out.getvalue().splitlines()
    assert lines == [
        "time,a",
        "00:00:00.000,1",
        "time,a,b",
        "00:00:00.000,1,2",
    ]


def test_csv_value_with_comma_is_quoted():
    out = io.StringIO()
    columns = [FakeColumn("note", "a,b"), FakeColumn("x", "1")]
    sampler = Sampler(columns, out=out, human=False)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[1] == '00:00:00.000,"a,b",1'


def test_csv_value_with_quote_is_doubled_and_quoted():
    out = io.StringIO()
    columns = [FakeColumn("note", 'say "hi"')]
    sampler = Sampler(columns, out=out, human=False)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[1] == '00:00:00.000,"say ""hi"""'


def test_csv_value_with_newline_stays_one_cell():
    out = io.StringIO()
    columns = [FakeColumn("note", "l1\nl2")]
    sampler = Sampler(columns, out=out, human=False)
    sampler.tick(0.0, MIDNIGHT)
    assert '"l1\nl2"' in out.getvalue()


def test_csv_header_name_with_comma_is_quoted():
    out = io.StringIO()
    columns = [FakeColumn("a,b", "1")]
    sampler = Sampler(columns, out=out, human=False)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[0] == 'time,"a,b"'
