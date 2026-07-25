#!/usr/bin/env python3
"""metawtf.terminal: ANSI scroll-region pinning for the human-mode header.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import shutil
import sys

CSI = "\033["


class PinnedHeader:
    """Freezes the header at the top of the screen via a DEC scroll region.

    The region (DECSTBM) confines scrolling to the rows below the header, so
    rows printed normally at the bottom scroll past while the header stays
    put. Content already in the terminal's scrollback is untouched; note that
    rows scrolled off the top of a scroll region are *not* added to
    scrollback by xterm-style terminals — redirect csv output to a file when
    a full record is needed. `close()` restores the full-screen region and
    drops the cursor below the output so the shell prompt lands cleanly.
    """

    def __init__(self, out=None, get_size=None):
        self.out = out or sys.stdout
        self.get_size = get_size or shutil.get_terminal_size
        self.is_active = False

    def show(self, header: str) -> None:
        # The sampler emits every header through one hook: the first sets the
        # pin up, later ones (column growth) redraw it in place.
        if self.is_active:
            self.draw_header(header)
        else:
            self.setup(header)

    def setup(self, header: str) -> None:
        size = self.get_size()
        rows = self.header_rows(header, size.columns)
        top = min(rows + 1, size.lines)
        self.write(
            f"{CSI}1;1H{header}\n"
            f"{CSI}{top};{size.lines}r"
            f"{CSI}{size.lines};1H"
        )
        self.is_active = True

    def draw_header(self, header: str) -> None:
        # Redraws in place: the column set can grow mid-run (hz match, json
        # expander) and the terminal can be resized, so the region is
        # re-issued from a fresh size on every redraw.
        size = self.get_size()
        rows = self.header_rows(header, size.columns)
        top = min(rows + 1, size.lines)
        cleared = "".join(
            f"{CSI}{row};1H{CSI}2K" for row in range(1, rows + 1)
        )
        self.write(
            f"\0337{cleared}{CSI}1;1H{header}{CSI}{top};{size.lines}r\0338"
        )

    def close(self) -> None:
        if not self.is_active:
            return
        self.is_active = False
        height = self.get_size().lines
        self.write(f"{CSI}r{CSI}{height};1H\n")

    def header_rows(self, header: str, columns: int) -> int:
        # A header wider than the terminal wraps; the region must start below
        # the wrapped rows or the tail of the header scrolls away.
        return max(1, -(-len(header) // max(1, columns)))

    def write(self, text: str) -> None:
        self.out.write(text)
        self.out.flush()
