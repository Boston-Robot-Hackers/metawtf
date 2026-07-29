#!/usr/bin/env python3
"""metawtf.terminal: ANSI scroll-region pinning for the human-mode header.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re
import shutil
import sys

CSI = "\033["

# ANSI SGR (Select Graphic Rendition) escape sequences: ESC [ ... m.
ANSI_SGR_RE = re.compile(r"\033\[[0-9;]*m")


def visual_length(text: str) -> int:
    """Return the number of visible columns a string occupies.

    ANSI color/formatting escape sequences have zero width, so they are stripped
    before measuring.  This keeps terminal wrapping calculations correct even
    when headers contain colored cells.
    """
    return len(ANSI_SGR_RE.sub("", text))


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
        # Clear first so the header starts alone on a clean screen instead of
        # amid whatever the terminal already showed, where it is easy to miss.
        size = self.get_size()
        rows = self.header_rows(header, size.columns)
        top = min(rows + 1, size.lines)
        self.write(
            f"{CSI}2J{CSI}1;1H{header}\n"
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
        # the wrapped rows or the tail of the header scrolls away.  Each physical
        # line is measured separately so ANSI color codes and multi-line headers
        # (group header + column header) are counted correctly.
        lines = header.splitlines()
        return max(
            1,
            sum(
                -(-visual_length(line) // max(1, columns))
                for line in lines
            ),
        )

    def write(self, text: str) -> None:
        self.out.write(text)
        self.out.flush()
