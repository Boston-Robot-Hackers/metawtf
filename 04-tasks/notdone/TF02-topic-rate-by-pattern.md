# TF02 — Topic rate (hz) by pattern, tasks for Feature F02

Depends on F01 (config loader, sampler, QoS helper, node scaffold). Tests use
fake graph / fake clock so they run without a live ROS graph.

## T01 — Schema: hz entries
**Status**: done — `HzColumn` + `parse_hz_column` in `metawtf/config.py`;
9 new tests in `test/test_config.py` (all pass). `metric: hz` takes exactly
one of `topic`/`match` (regex compiled at load), optional `window` (default
2.0, must be >= sample period), `name` forbidden with `match`.
**Description**: Extend the column schema: `metric: hz` takes exactly one of
`topic` (single topic) or `match` (regex, compiled at load; invalid regex →
clear error). Optional `window` in seconds, default 2.0, must be >= the sample
period. `name` is forbidden with `match` (column names come from topic names),
optional with `topic`.
**Test**: Unit test — hz and echo entries parse to expected structs; both
`topic`+`match` present, neither present, bad regex, `window` too small, `name`
with `match` → clear errors.

## T02 — Graph topic matcher
**Status**: done — `metawtf/topic_match.py` (`match_topics`); 4 tests in
`test/test_topic_match.py`. Regex `search` vs graph names, single-type pairs
returned, multi-type skipped with a `logging` warning, no match → empty list.
**Description**: Given a compiled regex and the graph's
`get_topic_names_and_types`, return matching `(topic, type)` pairs; type lists
flattened, multi-type topics skipped with a warning. No match → empty list.
**Test**: Unit test with an injected fake topic list — regex selects the right
topics and their types; multi-type skipped; no match → empty.

## T03 — Rolling-window rate counter
**Status**: done — `metawtf/rate_counter.py` (`RateCounter`); 6 tests in
`test/test_rate_counter.py`. Injectable clock; prunes entries older than
`window`; span-based `(n-1)/(t_newest-t_oldest)`; n<2 or zero span → None.
**Description**: Per topic, record arrival times in a deque (injectable clock).
`rate(now)`: prune entries older than `window`; with n >= 2 arrivals return
(n−1)/(t_newest − t_oldest), else None. This span-based estimator matches
`ros2 topic hz` and avoids the startup under-report of count/window.
**Test**: Unit test with a fake clock — steady 10 msg/s over a 2 s window ≈
10 hz; 3 messages in the first 0.2 s already reads 10 hz (not 1.5); a single
message → None; old entries pruned.

## T04 — Hz column via raw subscription
**Status**: done — `metawtf/hz_column.py` (`HzColumnState`); 4 tests in
`test/test_hz_column.py`. State records arrivals and formats the rolling rate
`%.3f`; name derived from topic via `from_topic`. The `raw=True` subscription
itself is created by the manager (T05) with `raw=sub.raw`.
**Description**: Create subscriptions with `raw=True` and record only the
arrival time — the serialized payload is never touched. Column name derived
from the topic (leading `/` stripped, remaining `/` → `_`). `sample()` returns
the rate formatted `%.3f`, or None.
**Test**: Unit test — callback with a fake serialized message records an
arrival; naming rules; exact format string.

## T05 — Dynamic subscription manager
**Status**: done — `metawtf/column_manager.py` (`ColumnManager`); 5 tests in
`test/test_column_manager.py` (fake node + fake graph). Handles echo and
single-topic hz (subscribe once topic appears) and `match` specs (append a
column + raw sub per newly matched topic); no duplicate subs; vanished topics
keep their column. `tracer_node.py` now delegates to it.
**Description**: On a periodic rescan (1 Hz timer), match graph topics, create
raw subscriptions (auto QoS, type from graph) for new matches, each feeding its
own rate counter. Never duplicate a subscription. Vanished topics keep their
column with empty cells.
**Test**: Unit test with a fake graph + fake node — first scan creates N subs;
second scan with one new topic creates exactly one more; no duplicates.

## T06 — Dynamic columns + header reprint
**Status**: done — `metawtf/sampler.py` reprints the header whenever the column
count changes; test `test_header_reprinted_when_column_added` in
`test/test_sampler.py`.
**Description**: Sampler supports the column set growing: when a rescan adds a
column, print a fresh header line before the next row. Document the
spreadsheet caveat in the sample config.
**Test**: Unit test — captured stdout shows header, rows, new header with the
added column, then rows with the extra cell.

## T07 — Feature test suite + demo verification
**Status**: partial — T01–T06 pass together (77 tests green on Jazzy). Still
owed: the live `match: "^/tf"` demo with a late-starting second tf topic
showing a reprinted header. A live echo+time+width demo against `/chatter` has
been run; the tf-match demo has not.
**Description**: T01–T06 pass together; sample config with `match: "^/tf"`;
run the demo against a live tf publisher plus a late-starting second tf topic.
**Test**: `colcon test --packages-select metawtf` green; demo shows rate lines
and a reprinted header with the new column.
