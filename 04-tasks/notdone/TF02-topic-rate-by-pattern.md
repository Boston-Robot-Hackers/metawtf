# TF02 — Topic rate (hz) by pattern, tasks for Feature F02

Depends on F01 (config loader, sampler, QoS helper, node scaffold). Tests use
fake graph / fake clock so they run without a live ROS graph.

## T01 — Schema: hz entries
**Status**: not done
**Description**: Extend the column schema: `metric: hz` takes exactly one of
`topic` (single topic) or `match` (regex, compiled at load; invalid regex →
clear error). Optional `window` in seconds, default 2.0, must be >= the sample
period. `name` is forbidden with `match` (column names come from topic names),
optional with `topic`.
**Test**: Unit test — hz and echo entries parse to expected structs; both
`topic`+`match` present, neither present, bad regex, `window` too small, `name`
with `match` → clear errors.

## T02 — Graph topic matcher
**Status**: not done
**Description**: Given a compiled regex and the graph's
`get_topic_names_and_types`, return matching `(topic, type)` pairs; type lists
flattened, multi-type topics skipped with a warning. No match → empty list.
**Test**: Unit test with an injected fake topic list — regex selects the right
topics and their types; multi-type skipped; no match → empty.

## T03 — Rolling-window rate counter
**Status**: not done
**Description**: Per topic, record arrival times in a deque (injectable clock).
`rate(now)`: prune entries older than `window`; with n >= 2 arrivals return
(n−1)/(t_newest − t_oldest), else None. This span-based estimator matches
`ros2 topic hz` and avoids the startup under-report of count/window.
**Test**: Unit test with a fake clock — steady 10 msg/s over a 2 s window ≈
10 hz; 3 messages in the first 0.2 s already reads 10 hz (not 1.5); a single
message → None; old entries pruned.

## T04 — Hz column via raw subscription
**Status**: not done
**Description**: Create subscriptions with `raw=True` and record only the
arrival time — the serialized payload is never touched. Column name derived
from the topic (leading `/` stripped, remaining `/` → `_`). `sample()` returns
the rate formatted `%.3f`, or None.
**Test**: Unit test — callback with a fake serialized message records an
arrival; naming rules; exact format string.

## T05 — Dynamic subscription manager
**Status**: not done
**Description**: On a periodic rescan (1 Hz timer), match graph topics, create
raw subscriptions (auto QoS, type from graph) for new matches, each feeding its
own rate counter. Never duplicate a subscription. Vanished topics keep their
column with empty cells.
**Test**: Unit test with a fake graph + fake node — first scan creates N subs;
second scan with one new topic creates exactly one more; no duplicates.

## T06 — Dynamic columns + header reprint
**Status**: not done
**Description**: Sampler supports the column set growing: when a rescan adds a
column, print a fresh header line before the next row. Document the
spreadsheet caveat in the sample config.
**Test**: Unit test — captured stdout shows header, rows, new header with the
added column, then rows with the extra cell.

## T07 — Feature test suite + demo verification
**Status**: not done
**Description**: T01–T06 pass together; sample config with `match: "^/tf"`;
run the demo against a live tf publisher plus a late-starting second tf topic.
**Test**: `colcon test --packages-select metawtf` green; demo shows rate lines
and a reprinted header with the new column.
