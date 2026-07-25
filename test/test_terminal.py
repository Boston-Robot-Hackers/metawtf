#!/usr/bin/env python3
"""Tests for metawtf.terminal.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import io
import os

from metawtf.terminal import PinnedHeader

SIZE_80X24 = os.terminal_size((80, 24))


def make_pinned(out, size=SIZE_80X24):
    return PinnedHeader(out=out, get_size=lambda: size)


def test_setup_draws_header_and_pins_region_below_it():
    out = io.StringIO()
    pinned = make_pinned(out)
    pinned.setup("time, a")
    assert out.getvalue() == "\033[1;1Htime, a\n\033[2;24r\033[24;1H"
    assert pinned.is_active is True


def test_setup_counts_wrapped_header_rows():
    out = io.StringIO()
    pinned = make_pinned(out)
    header = "x" * 90  # wraps to two rows on an 80-column terminal
    pinned.setup(header)
    assert out.getvalue() == f"\033[1;1H{header}\n\033[3;24r\033[24;1H"


def test_setup_clamps_region_when_header_fills_the_screen():
    out = io.StringIO()
    pinned = make_pinned(out, size=os.terminal_size((10, 3)))
    pinned.setup("x" * 40)  # 4 wrapped rows on a 3-line terminal
    assert "\033[3;3r" in out.getvalue()


def test_draw_header_clears_and_reprints_in_place():
    out = io.StringIO()
    pinned = make_pinned(out)
    pinned.setup("time, a")
    out.seek(0)
    out.truncate(0)
    pinned.draw_header("time, a, b")
    assert out.getvalue() == (
        "\0337\033[1;1H\033[2K\033[1;1Htime, a, b\033[2;24r\0338"
    )


def test_draw_header_reissues_region_from_a_fresh_size():
    out = io.StringIO()
    size = os.terminal_size((80, 24))
    pinned = PinnedHeader(out=out, get_size=lambda: size)
    pinned.setup("time, a")
    size = os.terminal_size((80, 40))  # resized taller
    out.seek(0)
    out.truncate(0)
    pinned.draw_header("time, a")
    assert "\033[2;40r" in out.getvalue()


def test_close_resets_region_and_drops_cursor_below_output():
    out = io.StringIO()
    pinned = make_pinned(out)
    pinned.setup("time, a")
    out.seek(0)
    out.truncate(0)
    pinned.close()
    assert out.getvalue() == "\033[r\033[24;1H\n"
    assert pinned.is_active is False


def test_close_is_idempotent():
    out = io.StringIO()
    pinned = make_pinned(out)
    pinned.setup("time, a")
    pinned.close()
    out.seek(0)
    out.truncate(0)
    pinned.close()
    assert out.getvalue() == ""


def test_close_without_setup_is_a_noop():
    out = io.StringIO()
    make_pinned(out).close()
    assert out.getvalue() == ""


def test_show_sets_up_on_first_header_and_redraws_after():
    out = io.StringIO()
    pinned = make_pinned(out)
    pinned.show("time, a")
    assert out.getvalue() == "\033[1;1Htime, a\n\033[2;24r\033[24;1H"
    pinned.show("time, a, b")
    assert out.getvalue().endswith(
        "\0337\033[1;1H\033[2K\033[1;1Htime, a, b\033[2;24r\0338"
    )
