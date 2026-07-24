#!/usr/bin/env python3
"""metawtf.column_manager: own column states and (re)subscribe to topics.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import json
import time
from dataclasses import dataclass

from metawtf.config import (
    Config,
    EchoColumn,
    ProcCpuColumn,
    SysCpuColumn,
    subfield_name,
)
from metawtf.echo_column import EchoColumnState
from metawtf.field_extract import FieldPathError, extract_field
from metawtf.hz_column import HzColumnState
from metawtf.json_column import JsonEchoColumnState
from metawtf.msg_type import (
    MessageTypeError,
    TopicNotFoundError,
    resolve_message_type,
)
from metawtf.proc_cpu_column import ProcCpuColumnState
from metawtf.qos_select import select_qos
from metawtf.sys_cpu_column import SysCpuColumnState
from metawtf.topic_match import match_topics


@dataclass
class Subscription:
    states: list
    topic: str
    configured_type: str | None
    raw: bool
    subscribed: bool = False
    failed: bool = False


@dataclass
class MatchSpec:
    pattern: object
    window: float
    width: int | None


class ColumnManager:
    """Builds the sampler's column list and creates subscriptions lazily.

    Echo and single-topic hz columns are fixed from config and subscribe once
    their topic appears. `match` hz specs and `json` echo columns without an
    explicit key list grow the column set at runtime, so the sampler reprints
    its header. One subscription may feed several column states (an echo `json`
    column with `subfields`, or a discovered set of keys). `proc_cpu` and
    `sys_cpu` columns have no topic at all: their states are fixed from config
    and sample /proc.
    """

    def __init__(self, node, config: Config):
        self.node = node
        self.states = []
        self.subscriptions = []
        self.match_specs = []
        self.matched_topics = set()
        for column in config.columns:
            self.add_config_column(column)

    def add_config_column(self, column) -> None:
        if isinstance(column, EchoColumn):
            self.add_echo_column(column)
        elif isinstance(column, ProcCpuColumn):
            # No topic, no subscription: the state samples /proc on each tick.
            state = ProcCpuColumnState(
                column.name, column.process, column.width
            )
            self.states.append(state)
        elif isinstance(column, SysCpuColumn):
            # Same shape as proc_cpu: no topic, the state reads /proc/stat.
            state = SysCpuColumnState(column.name, column.mode, column.width)
            self.states.append(state)
        elif column.match is not None:
            self.match_specs.append(
                MatchSpec(column.match, column.window, column.width)
            )
        else:
            state = HzColumnState(column.name, column.window, column.width)
            self.register([state], column.topic, None, raw=True)

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

    def register(self, states, topic, configured_type, raw) -> None:
        self.states.extend(states)
        self.subscriptions.append(
            Subscription(list(states), topic, configured_type, raw)
        )

    def register_expander(self, column: EchoColumn) -> None:
        # No columns yet; the expander discovers keys from the first message and
        # installs one JsonEchoColumnState per key into this subscription.
        sub = Subscription([], column.topic, column.type, raw=False)
        sub.states.append(JsonKeysExpander(self, sub, column))
        self.subscriptions.append(sub)

    def scan(self) -> bool:
        # The graph is queried once per scan and the snapshot handed down, not
        # once per pending subscription — those queries are DDS round-trips.
        names_and_types = self.node.get_topic_names_and_types()
        for sub in list(self.subscriptions):
            self.try_subscribe(sub, names_and_types)
        added = False
        for spec in self.match_specs:
            added = self.scan_match(spec, names_and_types) or added
        return added

    def scan_match(self, spec: MatchSpec, names_and_types) -> bool:
        added = False
        for topic, _type in match_topics(spec.pattern, names_and_types):
            if topic in self.matched_topics:
                continue
            self.matched_topics.add(topic)
            state = HzColumnState.from_topic(topic, spec.window, spec.width)
            self.register([state], topic, None, raw=True)
            self.try_subscribe(self.subscriptions[-1], names_and_types)
            added = True
        return added

    def try_subscribe(self, sub: Subscription, names_and_types) -> None:
        if sub.subscribed or sub.failed:
            return
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


class JsonKeysExpander:
    """Recipient placeholder that expands a `json` echo column with no explicit
    subfields into one column per top-level key of the first parsed message."""

    def __init__(self, manager: ColumnManager, subscription: Subscription,
                 column: EchoColumn):
        self.manager = manager
        self.subscription = subscription
        self.column = column
        self.expanded = False

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
            state = JsonEchoColumnState(
                subfield_name(self.column.name, key),
                self.column.field, key, self.column.stale_after, self.column.width,
            )
            self.manager.states.append(state)
            self.subscription.states.append(state)
            state.on_message(msg, now)


def make_callback(recipients):
    def callback(msg):
        now = time.monotonic()
        for state in list(recipients):
            state.on_message(msg, now)
    return callback
