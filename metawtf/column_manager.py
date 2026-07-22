#!/usr/bin/env python3
"""metawtf.column_manager: own column states and (re)subscribe to topics.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import time
from dataclasses import dataclass

from metawtf.config import Config, EchoColumn
from metawtf.echo_column import EchoColumnState
from metawtf.hz_column import HzColumnState
from metawtf.msg_type import (
    MessageTypeError,
    TopicNotFoundError,
    resolve_message_type,
)
from metawtf.qos_select import select_qos
from metawtf.topic_match import match_topics


@dataclass
class Subscription:
    state: object
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
    their topic appears. `match` hz specs discover topics on each scan and
    append a new column (and raw subscription) per newly matched topic, so the
    column list grows over the run. Vanished topics keep their column; their
    rate simply goes empty.
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
            state = EchoColumnState(
                column.name, column.field, column.stale_after, column.width
            )
            self.register(state, column.topic, column.type, raw=False)
        elif column.match is not None:
            self.match_specs.append(
                MatchSpec(column.match, column.window, column.width)
            )
        else:
            state = HzColumnState(column.name, column.window, column.width)
            self.register(state, column.topic, None, raw=True)

    def register(self, state, topic: str, configured_type: str | None, raw: bool):
        self.states.append(state)
        self.subscriptions.append(Subscription(state, topic, configured_type, raw))

    def scan(self) -> bool:
        for sub in list(self.subscriptions):
            self.try_subscribe(sub)
        added = False
        for spec in self.match_specs:
            added = self.scan_match(spec) or added
        return added

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
        callback = make_callback(sub.state)
        self.node.create_subscription(
            msg_class, sub.topic, callback, qos, raw=sub.raw
        )
        sub.subscribed = True


def make_callback(state):
    return lambda msg, state=state: state.on_message(msg, time.monotonic())
