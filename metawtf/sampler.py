#!/usr/bin/env python3
"""metawtf.sampler: build the header/rows for one sample tick.

Two render modes share the same cell collection: `csv` is pure RFC-4180 for
redirects and spreadsheets; `human` pads cells into aligned columns for a
terminal and truncates over-wide values so rows never drift.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import shutil
import sys
from datetime import datetime
from typing import Protocol, TextIO

from metawtf.config import PercentWidth, TimeColumn


class SampledColumn(Protocol):
    name: str
    width: int | PercentWidth | None
    kind: str

    def sample(self, now: float) -> str | None: ...


# ANSI foreground colors for each column kind in human mode.
KIND_COLORS = {
    "time": "\033[97m",     # bright white
    "echo": "\033[92m",     # bright green
    "hz": "\033[93m",       # bright yellow
    "proc_cpu": "\033[91m", # bright red
    "sys_cpu": "\033[96m",  # bright cyan
}
COLOR_RESET = "\033[0m"

# Labels used in the grouped kind header above the regular header.
GROUP_LABELS = {
    "time": "time",
    "echo": "echo",
    "hz": "hz",
    "proc_cpu": "proc",
    "sys_cpu": "syscpu",
}


def resolve_width(
    width: int | PercentWidth | None, terminal_columns: int
) -> int | None:
    """Turn a configured width into a concrete character count.

    A plain `int` (or `None`) passes through unchanged; a `PercentWidth` is
    resolved against the current terminal width, clamped to at least 1 so a
    tiny percentage never collapses a column to nothing.
    """
    if isinstance(width, PercentWidth):
        return max(1, round(width.percent / 100 * terminal_columns))
    return width


def colorize(text: str, kind: str) -> str:
    """Wrap text in the ANSI color for a column kind, if one is defined."""
    code = KIND_COLORS.get(kind)
    if code is None:
        return text
    return f"{code}{text}{COLOR_RESET}"


class Sampler:
    def __init__(
        self,
        columns: list[SampledColumn],
        time: TimeColumn | None = None,
        out: TextIO | None = None,
        *,
        human: bool,
        color: bool = False,
        on_header=None,
        get_size=None,
    ):
        self.columns = columns
        self.time = time or TimeColumn()
        self.out = out or sys.stdout
        self.human = human
        self.color = color and human
        # A pinned-header terminal intercepts header prints to redraw the
        # frozen header in place instead of scrolling a new one past.
        self.on_header = on_header
        self.header_width = None
        # Only human mode cares about terminal size (pinning, percent
        # widths); csv output ignores width entirely, so this stays unread.
        self.get_size = get_size or shutil.get_terminal_size
        self.last_size = None

    def tick(self, now_monotonic: float, now_wall: datetime) -> None:
        # The header is re-emitted whenever the column set grows (a `match`
        # hz spec discovers a new topic) or the terminal is resized: a plain
        # resize doesn't change header text, but the pinned scroll region and
        # any percent-based widths must still be recalculated for the new
        # size, and re-emitting is what triggers that recalculation.
        current_size = self.get_size() if self.human else None
        resized = self.human and current_size != self.last_size
        if self.header_width != len(self.columns) or resized:
            self.emit_header()
            self.header_width = len(self.columns)
            self.last_size = current_size
        print(self.format_row(now_monotonic, now_wall), file=self.out)

    def emit_header(self) -> None:
        header = self.format_header()
        if self.color:
            header = self.format_group_header() + "\n" + header
        if self.on_header is not None:
            self.on_header(header)
        else:
            print(header, file=self.out)

    def format_header(self) -> str:
        terminal_columns = self.terminal_columns()
        cells = [("time", resolve_width(self.time.width, terminal_columns))]
        cells += [
            (column.name, resolve_width(column.width, terminal_columns))
            for column in self.columns
        ]
        return self.join_row(cells, is_header=True)

    def format_row(self, now_monotonic: float, now_wall: datetime) -> str:
        terminal_columns = self.terminal_columns()
        stamp = format_timestamp(now_wall, self.time.format)
        cells = [(stamp, resolve_width(self.time.width, terminal_columns))]
        for column in self.columns:
            value = column.sample(now_monotonic)
            width = resolve_width(column.width, terminal_columns)
            cells.append(("" if value is None else value, width))
        return self.join_row(cells, is_header=False)

    def format_group_header(self) -> str:
        columns = [self.time] + list(self.columns)
        return join_group_header(columns, self.terminal_columns())

    def terminal_columns(self) -> int:
        # csv ignores width, so avoid the terminal query when it can't matter.
        return self.get_size().columns if self.human else 0

    def _column_kinds(self) -> list[str]:
        return ["time"] + [
            getattr(column, "kind", "unknown") for column in self.columns
        ]

    def join_row(
        self, cells: list[tuple[str, int | None]], is_header: bool
    ) -> str:
        if self.human:
            return join_human(
                cells, is_header, self._column_kinds(), color=self.color
            )
        return join_csv(cells)


def join_csv(cells: list[tuple[str, int | None]]) -> str:
    # Pure RFC-4180: no padding, bare commas, values never truncated.
    return ",".join(quote_cell(text) for text, _width in cells)


def join_human(
    cells: list[tuple[str, int | None]],
    is_header: bool,
    kinds: list[str] | None = None,
    color: bool = False,
) -> str:
    # The comma binds to the value it follows and padding comes after it, so
    # columns line up in the terminal; a single space always follows the
    # comma. Both are cut to the column width so nothing pushes a row's later
    # cells right of the header. A data value keeps its head (`…` at the end);
    # a header keeps its tail (`…` at the front) since the distinguishing part
    # of a name — e.g. the topic in `cpu_nav2` — is usually the end.
    parts = []
    last_index = len(cells) - 1
    for index, (text, width) in enumerate(cells):
        text = truncate_tail(text, width) if is_header else truncate(text, width)
        if index < last_index:
            text = f"{text}, "
            width = None if width is None else width + 2
        text = pad(text, width)
        if color and kinds is not None:
            text = colorize(text, kinds[index])
        parts.append(text)
    return "".join(parts)


def join_group_header(columns: list[SampledColumn], terminal_columns: int) -> str:
    """Build the kind-group header that sits above the column-name header.

    Contiguous columns of the same kind are merged into one colored cell whose
    visual width spans the underlying columns and their internal comma+space
    separators.  The kind label is centered inside each group and truncated if
    the group is too narrow.
    """
    groups = []
    i = 0
    n = len(columns)
    while i < n:
        kind = getattr(columns[i], "kind", "unknown")
        j = i + 1
        while j < n and getattr(columns[j], "kind", "unknown") == kind:
            j += 1
        group_width = 0
        for k in range(i, j):
            col = columns[k]
            width = resolve_width(col.width, terminal_columns)
            base = width if width is not None else len(col.name)
            group_width += base
            if k < n - 1:
                group_width += 2  # comma + space after every column but the last
        label = GROUP_LABELS.get(kind, kind)
        if group_width <= 0:
            label = ""
        elif len(label) > group_width:
            label = label[: group_width - 1] + "…" if group_width > 1 else label[:1]
        else:
            label = label.center(group_width)
        groups.append(colorize(label, kind))
        i = j
    return "".join(groups)


def truncate(text: str, width: int | None) -> str:
    if width is None or len(text) <= width:
        return text
    return text[: width - 1] + "…"


def truncate_tail(text: str, width: int | None) -> str:
    if width is None or len(text) <= width:
        return text
    return "…" + text[-(width - 1):]


def quote_cell(text: str) -> str:
    # A cell containing a comma, quote, or line break is wrapped in quotes with
    # inner quotes doubled, so a string value cannot corrupt the row's cells.
    if any(mark in text for mark in ',"\n\r'):
        return '"' + text.replace('"', '""') + '"'
    return text


def pad(text: str, width: int | None) -> str:
    # Left-justify to a minimum width; over-wide values are truncate()'s job,
    # applied before the comma suffix is added.
    if width is None:
        return text
    return text.ljust(width)


def format_timestamp(now_wall: datetime, fmt: str | None) -> str:
    # Default keeps millisecond precision, which strftime cannot express
    # directly; a configured strftime string takes over when present.
    if fmt is None:
        milliseconds = now_wall.microsecond // 1000
        return f"{now_wall:%H:%M:%S}.{milliseconds:03d}"
    return now_wall.strftime(fmt)
