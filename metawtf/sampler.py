#!/usr/bin/env python3
"""metawtf.sampler: build the CSV header/rows for one sample tick.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import sys
from datetime import datetime
from typing import Protocol, TextIO


class SampledColumn(Protocol):
    name: str

    def sample(self, now: float) -> str | None: ...


class Sampler:
    def __init__(self, columns: list[SampledColumn], out: TextIO = sys.stdout):
        self.columns = columns
        self.out = out
        self.header_printed = False

    def tick(self, now_monotonic: float, now_wall: datetime) -> None:
        if not self.header_printed:
            print(self.format_header(), file=self.out)
            self.header_printed = True
        print(self.format_row(now_monotonic, now_wall), file=self.out)

    def format_header(self) -> str:
        names = ",".join(column.name for column in self.columns)
        return f"time,{names}"

    def format_row(self, now_monotonic: float, now_wall: datetime) -> str:
        cells = [format_timestamp(now_wall)]
        for column in self.columns:
            value = column.sample(now_monotonic)
            cells.append("" if value is None else value)
        return ",".join(cells)


def format_timestamp(now_wall: datetime) -> str:
    milliseconds = now_wall.microsecond // 1000
    return f"{now_wall:%H:%M:%S}.{milliseconds:03d}"
