# TF02 — Topic rate (hz) by pattern, tasks for Feature F02

Depends on F01 (config loader, node scaffold, output). Tests use fake graph /
fake clock so they run without a live ROS graph.

## T01 — Extend config schema for metrics
**Status**: not done
**Description**: Parse unified entries: echo (`topic`+`fields`) and hz
(`match`+`window`), keyed by `metric`. Default `metric` and `window`. Validate.
**Test**: Unit test — hz entry and echo entry parse to expected structs; bad
`metric`, missing `match`, non-numeric `window` raise clear errors.

## T02 — Graph topic matcher
**Status**: not done
**Description**: Given a regex and the graph's topic list, return matching
`(topic, type)` pairs. Wraps `get_topic_names_and_types`; type list flattened.
**Test**: Unit test with an injected fake topic list — regex selects the right
topics and their types; no match → empty.

## T03 — Rate counter with rolling window
**Status**: not done
**Description**: Per topic, record message arrival times; compute hz over
`window`. Injectable clock. Drop timestamps older than the window.
**Test**: Unit test feeding timed arrivals against a fake clock — computed hz
matches expected within tolerance; empty window → 0 hz.

## T04 — Rate line formatter
**Status**: not done
**Description**: Format `HH:MM:SS <topic> <hz> hz (<n> msgs / <window>s)`.
**Test**: Unit test — fixed inputs produce exact expected string.

## T05 — Dynamic subscription manager
**Status**: not done
**Description**: On a periodic rescan, match graph topics, create subscriptions
for new matches (type from graph), feed each callback into its rate counter.
Avoid duplicate subscriptions.
**Test**: Unit test the manager with a fake graph + fake node — first scan
creates N subs, second scan with one new topic creates exactly one more, none
duplicated.

## T06 — Rate report timer
**Status**: not done
**Description**: Timer fires every `window`; for each tracked topic compute hz,
format, print. Integrate hz path alongside F01 echo path in the node.
**Test**: Unit test the timer callback with injected counters — prints expected
lines; echo entries unaffected.

## T07 — Feature test suite + demo verification
**Status**: not done
**Description**: T01–T06 pass together; sample config with `^/tf`; run demo
against live tf publisher to confirm real rates and late-topic pickup.
**Test**: `colcon test --packages-select metawtf` green; demo shows rate lines.
