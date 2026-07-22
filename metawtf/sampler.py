#!/usr/bin/env python3
"""metawtf.sampler: build the CSV header/rows for one sample tick.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import sys
from datetime import datetime
from typing import Protocol, TextIO

from metawtf.config import TimeColumn


class SampledColumn(Protocol):
    name: str
    width: int | None

    def sample(self, now: float) -> str | None: ...


class Sampler:
    def __init__(
        self,
        columns: list[SampledColumn],
        time: TimeColumn = None,
        out: TextIO = sys.stdout,
    ):
        self.columns = columns
        self.time = time or TimeColumn()
        self.out = out
        self.header_width = None

    def tick(self, now_monotonic: float, now_wall: datetime) -> None:
        # Columns can grow when a `match` hz spec discovers a new topic; reprint
        # the header so the added column is labelled (a documented CSV caveat).
        if self.header_width != len(self.columns):
            print(self.format_header(), file=self.out)
            self.header_width = len(self.columns)
        print(self.format_row(now_monotonic, now_wall), file=self.out)

    def format_header(self) -> str:
        cells = [("time", self.time.width)]
        cells += [(column.name, column.width) for column in self.columns]
        return join_cells(cells)

    def format_row(self, now_monotonic: float, now_wall: datetime) -> str:
        cells = [(format_timestamp(now_wall, self.time.format), self.time.width)]
        for column in self.columns:
            value = column.sample(now_monotonic)
            cells.append(("" if value is None else value, column.width))
        return join_cells(cells)


def join_cells(cells: list[tuple[str, int | None]]) -> str:
    # The comma binds to the value it follows and padding comes after it, so
    # columns line up in the terminal while the row still imports as CSV.
    parts = []
    last_index = len(cells) - 1
    for index, (text, width) in enumerate(cells):
        if index < last_index:
            text = f"{text},"
            width = None if width is None else width + 1
        parts.append(pad(text, width))
    return "".join(parts)


def pad(text: str, width: int | None) -> str:
    # Left-justify to a minimum width; never truncates.
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
