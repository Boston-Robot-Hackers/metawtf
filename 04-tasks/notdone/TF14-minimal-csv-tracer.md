# TF14 — Minimal CSV tracer

**Date Created:** 2026-10-22

## TF14.0 — Confirm LOC accounting and retained product scope

**Status**: not done
**Description**: Record the reproducible physical-line count for tracked
production Python modules plus `install.sh`; confirm the <=1,038-line target
and retained/removed behaviors before implementation.
**Test**: Re-run the tracked-file line count and verify the metric is measured
consistently against the 2,076-line starting baseline.

## TF14.1 — Revise the product contract

**Status**: not done
**Description**: Update `02-doc/spec.md`, README usage/configuration sections,
and example configs to describe the reduced CSV-only feature set and remove
references to removed capabilities.
**Test**: Review all documented directives and examples against the retained
configuration grammar.

## TF14.2 — Reduce configuration and field extraction

**Status**: not done
**Description**: Keep the smallest validated configuration needed for sample
rate, timestamp, and configured echo columns; remove width, JSON, multi-field,
and unsupported metric parsing while retaining clear errors for malformed
remaining config.
**Test**: Keep focused parser and field-extraction tests for valid configs,
invalid configs, scalar paths, and missing fields.

## TF14.3 — Remove unused metric families and dynamic discovery

**Status**: not done
**Description**: Remove `hz`, `proc_cpu`, and `sys_cpu` columns, regex topic
matching, associated trackers/parsers, and their no-longer-applicable tests.
Keep lazy subscription to configured echo topics.
**Test**: Verify configured echo subscriptions still wait for the topic,
resolve its message type, and sample incoming values.

## TF14.4 — Replace terminal UI with CSV sampling

**Status**: not done
**Description**: Remove human formatting, terminal pinning/color/width logic,
and interactive pause/help/quit controls. Keep timestamps and RFC-4180-safe
CSV cells on the sampling clock.
**Test**: Cover CSV quoting, timestamps, missing/stale values, and row cadence
through focused sampler tests.

## TF14.5 — Retain a complete test suite for the reduced product

**Status**: not done
**Description**: Add or update the dedicated retained-product tests, remove
tests only for intentionally removed behavior, and ensure test discovery runs
the retained suite under the repository's supported pytest/colcon paths.
**Test**: Run the full available pytest suite and colcon test where ROS2 is
available; record environment-specific limitations rather than masking them.

## TF14.6 — Reduce literate documentation

**Status**: not done
**Description**: Refresh literate chapters affected by removed modules and
update the overview to explain the reduced package architecture.
**Test**: Check that literate documentation references only retained modules
and behavior.

## TF14.7 — Verify size target and close out

**Status**: not done
**Description**: Recount tracked production LOC, resolve any remaining stale
references, and update feature/task completion status only after the full
retained test suite passes.
**Test**: Confirm production LOC is at or below 1,038 and all available
required tests pass.
