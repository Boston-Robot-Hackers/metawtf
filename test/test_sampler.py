#!/usr/bin/env python3
"""Tests for metawtf.sampler.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import io
import os
from datetime import datetime

from metawtf.config import PercentWidth, TimeColumn
from metawtf.sampler import Sampler, resolve_width
from metawtf.terminal import ANSI_SGR_RE

SIZE_80X24 = os.terminal_size((80, 24))
SIZE_40X24 = os.terminal_size((40, 24))


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


def test_long_header_truncates_to_its_tail():
    # cpu_nav2 (8 chars) in a width-6 column: the header keeps its tail so the
    # distinguishing topic suffix survives and header/rows stay aligned.
    out = io.StringIO()
    columns = [
        FakeColumn("cpu_nav2", "100.0%", width=6),
        FakeColumn("hz", "20.00", width=6),
    ]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, MIDNIGHT)
    lines = out.getvalue().splitlines()
    assert lines[0] == "time, …_nav2, hz    "
    assert lines[1] == "00:00:00.000, 100.0%, 20.00 "


def test_header_shorter_than_width_is_untouched():
    out = io.StringIO()
    columns = [FakeColumn("hz", "20.00", width=6)]
    sampler = Sampler(columns, out=out, human=True)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[0] == "time, hz    "


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


def test_color_group_header_with_default_time_column():
    # Regression: TimeColumn had no `name` attribute, so join_group_header's
    # `len(col.name)` fallback for an unset width crashed as soon as a real
    # run enabled --color (default TimeColumn width is None).
    out = io.StringIO()
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out, human=True, color=True)
    sampler.tick(0.0, MIDNIGHT)
    lines = [ANSI_SGR_RE.sub("", line) for line in out.getvalue().splitlines()]
    assert "time" in lines[0]
    assert lines[1] == "time, a"


def test_csv_header_name_with_comma_is_quoted():
    out = io.StringIO()
    columns = [FakeColumn("a,b", "1")]
    sampler = Sampler(columns, out=out, human=False)
    sampler.tick(0.0, MIDNIGHT)
    assert out.getvalue().splitlines()[0] == 'time,"a,b"'


def test_resolve_width_passes_through_plain_int_and_none():
    assert resolve_width(8, terminal_columns=80) == 8
    assert resolve_width(None, terminal_columns=80) is None


def test_resolve_width_computes_percent_of_terminal_columns():
    assert resolve_width(PercentWidth(25), terminal_columns=80) == 20


def test_resolve_width_clamps_percent_to_at_least_one():
    assert resolve_width(PercentWidth(1), terminal_columns=40) == 1


def test_header_reprinted_on_terminal_resize_with_no_column_change():
    # Regression: the pinned header used to redraw only when the column set
    # grew, so a plain vertical/horizontal resize left it un-repinned.
    out = io.StringIO()
    headers = []
    sizes = [SIZE_80X24]
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(
        columns, out=out, human=True,
        on_header=headers.append, get_size=lambda: sizes[0],
    )
    sampler.tick(0.0, MIDNIGHT)
    sizes[0] = SIZE_40X24
    sampler.tick(1.0, MIDNIGHT)
    assert len(headers) == 2


def test_header_not_reprinted_when_size_is_unchanged():
    out = io.StringIO()
    headers = []
    columns = [FakeColumn("a", "1")]
    sampler = Sampler(
        columns, out=out, human=True,
        on_header=headers.append, get_size=lambda: SIZE_80X24,
    )
    sampler.tick(0.0, MIDNIGHT)
    sampler.tick(1.0, MIDNIGHT)
    assert len(headers) == 1


def test_csv_mode_ignores_resize_and_never_queries_terminal_size():
    out = io.StringIO()

    def explode():
        raise AssertionError("csv mode must not query terminal size")

    columns = [FakeColumn("a", "1")]
    sampler = Sampler(columns, out=out, human=False, get_size=explode)
    sampler.tick(0.0, MIDNIGHT)
    sampler.tick(1.0, MIDNIGHT)
    assert out.getvalue().splitlines()[0] == "time,a"


def test_percent_width_column_scales_with_terminal_width():
    out = io.StringIO()
    columns = [FakeColumn("cpu", "1.5", width=PercentWidth(50))]
    sampler = Sampler(columns, out=out, human=True, get_size=lambda: SIZE_40X24)
    sampler.tick(0.0, MIDNIGHT)
    lines = out.getvalue().splitlines()
    # 50% of 40 columns == 20 chars; "cpu"/"1.5" (3 chars) pad out the rest.
    assert lines[0] == "time, cpu" + " " * 17
    assert lines[1] == "00:00:00.000, 1.5" + " " * 17


def test_percent_width_column_re_resolves_after_resize():
    out = io.StringIO()
    sizes = [SIZE_40X24]
    columns = [FakeColumn("cpu", "1.5", width=PercentWidth(50))]
    sampler = Sampler(columns, out=out, human=True, get_size=lambda: sizes[0])
    sampler.tick(0.0, MIDNIGHT)
    sizes[0] = os.terminal_size((80, 24))
    sampler.tick(1.0, MIDNIGHT)
    lines = out.getvalue().splitlines()
    # Second header reflects 50% of the new 80-column width == 40 chars.
    assert lines[2] == "time, cpu" + " " * 37
