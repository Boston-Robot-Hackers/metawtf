---
version: "1.1"
generated: "2026-07-22"
---

# Column manager: one place that owns subscriptions

Early in F01 the node itself created echo subscriptions inline. F02 adds two new
shapes — single-topic hz columns and regex `match` columns that spawn new
columns at runtime — and doing all three inside the node would have turned it
into a tangle. `metawtf/column_manager.py` extracts that responsibility into
`ColumnManager`: it owns the list of column states the sampler iterates, and it
owns the logic that lazily subscribes each one as its topic appears.

Crucially, it depends on a *node-like object*, not on `rclpy`. Anything offering
`get_topic_names_and_types`, `get_publishers_info_by_topic`,
`create_subscription`, and `get_logger` will do — which is how
`test_column_manager.py` drives the whole thing with a fake node and asserts on
which subscriptions were made.

## Echo and hz are almost the same subscription

The key realization that keeps this module small: an echo subscription and an hz
subscription differ in only two ways — the `raw` flag, and (for echo) a
configured message type. Both callbacks are literally `state.on_message(msg,
now)`. F04 added one generalization: a single subscription may feed *several*
column states (one per JSON subfield), so the record holds a list:

```python
@dataclass
class Subscription:
    states: list
    topic: str
    configured_type: str | None
    raw: bool
    subscribed: bool = False
    failed: bool = False
```

Building the initial column set is a three-way branch on the config column,
with echo handling split out because it now has three shapes of its own:

```python
    def add_config_column(self, column) -> None:
        if isinstance(column, EchoColumn):
            self.add_echo_column(column)
        elif column.match is not None:
            self.match_specs.append(
                MatchSpec(column.match, column.window, column.width)
            )
        else:
            state = HzColumnState(column.name, column.window, column.width)
            self.register([state], column.topic, None, raw=True)
```

Echo and single-topic hz columns register a fixed `Subscription` immediately (to
be filled once the topic exists). A `match` column registers no column yet — it
becomes a `MatchSpec` that produces columns later.

## Echo's three shapes: plain, subfields, and discovered keys

```python
    def add_echo_column(self, column: EchoColumn) -> None:
        if column.subfields is not None:
            states = [
                JsonEchoColumnState(
                    name, column.field, key, column.stale_after, column.width,
                )
                for name, key in zip(column.subfield_names, column.subfields)
            ]
            self.register(states, column.topic, column.type, raw=False)
        elif column.is_json:
            self.register_expander(column)
        else:
            state = EchoColumnState(
                column.name, column.field, column.stale_after, column.width
            )
            self.register([state], column.topic, column.type, raw=False)
```

An explicit `subfields:` list fans out at config time: one
`JsonEchoColumnState` per key, all sharing one subscription (the column names
were already computed by `config.py`, keeping naming policy in one place).
`json: true` *without* subfields can't know its columns until a message
arrives, so it registers a `JsonKeysExpander` instead:

```python
class JsonKeysExpander:
    def on_message(self, msg, now: float) -> None:
        if self.expanded:
            return
        try:
            data = json.loads(extract_field(msg, self.column.field))
        except (FieldPathError, ValueError, TypeError):
            return  # wait for a well-formed message before fixing the columns
        if not isinstance(data, dict):
            return
        self.expanded = True
        for key in data:
            state = JsonEchoColumnState(...)
            self.manager.states.append(state)
            self.subscription.states.append(state)
            state.on_message(msg, now)
```

The expander is a *recipient impostor*: it sits in the subscription's
`states` list looking like a column state, but instead of holding a value it
waits for the first parseable message, then installs one real column per
top-level key — in the dict's insertion order, which for JSON is the order
the keys appeared in the message. Growing `manager.states` triggers the
sampler's header reprint (the same mechanism F02's `match` columns use). The
column set is then *fixed*: keys appearing only in later messages are ignored,
and a missing key renders `?` — a documented caveat that keeps the CSV shape
stable. Note the final `state.on_message(msg, now)`: the message that revealed
the keys also supplies their first values, so the trigger row isn't blank.

## Scanning: fixed subscriptions plus discovered ones

```python
    def scan(self) -> bool:
        for sub in list(self.subscriptions):
            self.try_subscribe(sub)
        added = False
        for spec in self.match_specs:
            added = self.scan_match(spec) or added
        return added
```

`scan` runs at construction and then on a 1 Hz timer. Each pass retries every
not-yet-subscribed fixed column (so a late-starting topic still connects), then
expands every match spec. `scan_match` is where the column list grows:

```python
    def scan_match(self, spec: MatchSpec) -> bool:
        names_and_types = self.node.get_topic_names_and_types()
        added = False
        for topic, _type in match_topics(spec.pattern, names_and_types):
            if topic in self.matched_topics:
                continue
            self.matched_topics.add(topic)
            state = HzColumnState.from_topic(topic, spec.window, spec.width)
            self.register(state, topic, None, raw=True)
            self.try_subscribe(self.subscriptions[-1])
            added = True
        return added
```

`matched_topics` is the dedup set that guarantees "never subscribe to the same
topic twice," even across rescans or overlapping patterns. A topic that later
vanishes is deliberately *not* removed: its column stays, and its rate simply
decays to empty — matching the F02 promise that columns don't disappear
mid-run. The `bool` return bubbles up "the column set grew," which the sampler
uses to reprint its header.

```mermaid
flowchart TD
    S[scan] --> F[retry fixed subs]
    S --> M{for each match spec}
    M --> MT[match_topics vs graph]
    MT --> NT{new topic?}
    NT -->|already known| Skip[skip]
    NT -->|new| NC[make HzColumnState + register + subscribe]
    NC --> G[return added = true]
```

## Subscribing: validate at the boundary, then trust

```python
    def try_subscribe(self, sub: Subscription) -> None:
        if sub.subscribed or sub.failed:
            return
        names_and_types = self.node.get_topic_names_and_types()
        try:
            msg_class = resolve_message_type(
                sub.topic, sub.configured_type, names_and_types
            )
        except TopicNotFoundError:
            return
        except MessageTypeError as error:
            self.node.get_logger().error(str(error))
            sub.failed = True
            return
        qos = select_qos(self.node.get_publishers_info_by_topic(sub.topic))
        callback = make_callback(sub.states)
        self.node.create_subscription(
            msg_class, sub.topic, callback, qos, raw=sub.raw
        )
        sub.subscribed = True
```

The two exceptions are treated very differently, and that difference matters. A
`TopicNotFoundError` is *transient* — the topic may appear later — so the
subscription is left pending and retried next scan. A `MessageTypeError` (a bad
configured type, or a genuinely multi-type topic) will not fix itself, so the
column is marked `failed` and never retried, which prevents the same error from
being logged once per second forever.

`make_callback` closes over the subscription's *list* of recipients rather
than a single state, and iterates a copy on each delivery:

```python
def make_callback(recipients):
    def callback(msg):
        now = time.monotonic()
        for state in list(recipients):
            state.on_message(msg, now)
    return callback
```

The `list(recipients)` copy matters: the `JsonKeysExpander` mutates that very
list from inside its own `on_message` (appending the freshly discovered column
states), and mutating a list while iterating it is undefined behavior worth
never risking. Taking `time.monotonic()` once per delivery also gives every
fan-out column the identical arrival timestamp.

## Observations for future improvement

- **QoS is chosen once, at subscribe time.** If a topic's publishers change
  their QoS after we connect, we don't renegotiate. Rare, but a periodic re-check
  could be added for long-running traces.
- **`Subscription.states` is typed `list`.** Its members are column states or
  a `JsonKeysExpander`; a small protocol type (`on_message(msg, now)`) would
  document the contract the callback relies on.
- **Shared JSON parsing.** Sibling subfield columns each re-parse the same
  JSON string per message; a fan-out that parses once would remove the
  duplicate work if wide JSON topics appear.
- **A vanished topic keeps consuming a column slot forever.** Intentional for
  now, but a very long run against a churning graph could accumulate empty
  columns; an optional prune could be offered later.
