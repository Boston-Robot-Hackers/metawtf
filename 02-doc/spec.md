# metawtf — Specification

A customizable trace tool.

## Overview

A line-oriented `metawtf.conf` config declares a set of metric columns — topic
field values, topic rates, process and system CPU. The tool samples all columns
on a common timer and prints one row per tick (timestamp plus one value per
column) to stdout.

Output comes in two formats. On a terminal the default is `human`: aligned,
padded columns, values wider than their column truncated with `…`, and the
header pinned to the top of the screen via an ANSI scroll region so rows
scroll beneath it. Piped or redirected output defaults to `csv`: plain
RFC-4180 rows, full untruncated values, no padding — ready for spreadsheets
and graphing. A `format human|csv` directive overrides the auto-detection.

## Goals

Make it easy to cook up a quick report for multiple things that happen at the
same time inside ROS2. Output must import into a spreadsheet and graph without
further processing.

## Non-Goals

General tool with a gui, a replacement for ros2 topic commands etc.
