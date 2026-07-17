# metawtf — Specification

A customizable trace tool.

## Overview

A YAML config declares a set of metric columns — topic field values, topic
rates, process CPU. The tool samples all columns on a common timer and prints
one CSV row per tick (timestamp plus one value per column) to stdout. The same
stream is eyeballed live and redirected to a file for spreadsheets and
graphing.

## Goals

Make it easy to cook up a quick report for multiple things that happen at the
same time inside ROS2. Output must import into a spreadsheet and graph without
further processing.

## Non-Goals

General tool with a gui, a replacement for ros2 topic commands etc.
