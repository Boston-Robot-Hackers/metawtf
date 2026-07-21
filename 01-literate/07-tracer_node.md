---
version: "1.0"
generated: "2026-07-21"
---

# Tracer Node: wiring config, subscriptions, and the sampler into one process

`metawtf/tracer_node.py` is the top of the dependency stack — it is the only
module that imports `rclpy` at module scope, and the only one that knows
about "a running program with a config file and a Ctrl-C." Every other
module in this codebase (`config`, `field_extract`, `msg_type`,
`qos_select`, `echo_column`, `sampler`) is pure logic that `TracerNode`
assembles into something that actually subscribes to topics and prints CSV.

## Lazy subscription: the topic you want might not exist yet

A robot's nodes don't all start at once. If `metawtf` required every
configured topic to already be publishing at startup, it would be unusable
as a "start it early and watch things come up" tool. Instead, each column
starts unsubscribed, and a 1 Hz timer keeps retrying:

```python
    def try_subscribe(self, index: int) -> None:
        if self.is_subscribed[index]:
            return
        column = self.config_columns[index]
        try:
            names_and_types = self.get_topic_names_and_types()
            msg_class = resolve_message_type(
                column.topic, column.type, names_and_types
            )
        except TopicNotFoundError:
            return
        except MessageTypeError as error:
            self.get_logger().error(str(error))
            return
        qos = select_qos(self.get_publishers_info_by_topic(column.topic))
        state = self.states[index]
        self.create_subscription(
            msg_class,
            column.topic,
            lambda msg, state=state: state.on_message(msg, time.monotonic()),
            qos,
        )
        self.is_subscribed[index] = True

    def rescan(self) -> None:
        for index in range(len(self.config_columns)):
            self.try_subscribe(index)
```

The two exceptions from `msg_type.py` earn their keep here: a
`TopicNotFoundError` is swallowed silently and retried next second — exactly
the "topic isn't up yet" case the feature spec calls out — while a
`MessageTypeError` (a multi-type topic, or a bad `type:` string) gets logged
once and then left alone; retrying wouldn't help, since neither problem
resolves itself over time.

```mermaid
sequenceDiagram
    participant Init as __init__
    participant Rescan as rescan (1 Hz)
    participant Sub as try_subscribe
    participant ROS as ROS graph

    Init->>Sub: try_subscribe(0) at startup
    Sub->>ROS: get_topic_names_and_types()
    ROS-->>Sub: topic not found
    Note over Sub: leaves is_subscribed[0] = False
    loop every 1s
        Rescan->>Sub: try_subscribe(0)
        Sub->>ROS: get_topic_names_and_types()
    end
    ROS-->>Sub: topic now found, one type
    Sub->>ROS: get_publishers_info_by_topic
    Sub->>Sub: select_qos(...)
    Sub->>Sub: create_subscription(...)
    Note over Sub: is_subscribed[0] = True; rescan skips it from now on
```

The `lambda msg, state=state: ...` default-argument trick is the standard
fix for Python's late-binding closures in a loop — without capturing `state`
as a default argument, every subscription's callback would close over the
same final value of the loop variable rather than its own column's state.

## Two independent timers, two different jobs

```python
        self.create_timer(RESCAN_PERIOD_SEC, self.rescan)
        self.create_timer(1.0 / config.sample_hz, self.on_tick)
```

`rescan` and `on_tick` run at unrelated cadences for unrelated reasons: the
1 Hz rescan is a discovery mechanism (cheap enough to run constantly, no
need to tie it to the sample rate), while `on_tick` runs at whatever rate
the user configured for output. Because `rclpy`'s default executor is
single-threaded, these two timers — and every subscription callback — never
run concurrently with each other, which is exactly why `on_message` in
`echo_column.py` can be a plain, lock-free field assignment.

## `main()`: the only place that talks to the OS

```python
def main(args=None) -> None:
    rclpy.init(args=args)
    config_path = Path.cwd() / CONFIG_FILENAME
    config = load_config(config_path)
    node = TracerNode(config)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
```

`metawtf.yaml` is resolved relative to the current working directory, not
the installed package — matching the demo workflow in F01 ("edit
`metawtf.yaml`, then `ros2 run metawtf metawtf` from that directory"). A
command-line override for the config path is an explicit non-goal of v1.
The `finally` block guarantees `destroy_node()`/`shutdown()` run even on
Ctrl-C, which matters for `rclpy` — leaking a node handle across repeated
runs inside the same process (as happens in the test suite) causes
increasingly confusing errors on the *next* `rclpy.init()`.

## Observations for future improvement

- **`is_subscribed` as a parallel list.** Indexing `self.states[index]`,
  `self.config_columns[index]`, and `self.is_subscribed[index]` together is
  a "parallel arrays" pattern the style guide's data-clump guidance flags.
  A small `ColumnBinding` dataclass (config, state, is_subscribed) indexed
  by a single list would read more clearly and remove the risk of the three
  lists drifting out of sync.
- **Untested end-to-end.** This module needs a real ROS2 install to import
  at all (`rclpy` isn't available in this dev environment); its tests are
  written with `pytest.importorskip("rclpy")` and currently skip. Verifying
  `try_subscribe`'s two exception branches against a real multi-publisher,
  multi-type graph is still outstanding — tracked in
  `04-tasks/notdone/TF01-config-driven-topic-trace.md`, task T07.
- **Rescanning every column every second is O(columns) graph calls.** Fine
  at trace-tool scale (a handful of columns), but if a config ever grows to
  dozens of columns, batching the graph query once per rescan (instead of
  once per still-unsubscribed column) would cut redundant
  `get_topic_names_and_types()` calls.
