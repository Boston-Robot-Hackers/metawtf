#!/usr/bin/env python3
"""Tests for metawtf.column_manager.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re
from types import SimpleNamespace

from metawtf.column_manager import ColumnManager
from metawtf.config import Config, EchoColumn, HzColumn


class FakeLogger:
    def error(self, message):
        pass


class FakeNode:
    def __init__(self, names_and_types):
        self.names_and_types = names_and_types
        self.subscriptions_made = []
        self.callbacks = {}
        self.graph_queries = 0

    def get_topic_names_and_types(self):
        self.graph_queries += 1
        return self.names_and_types

    def get_publishers_info_by_topic(self, topic):
        return []

    def create_subscription(self, msg_class, topic, callback, qos, raw=False):
        self.subscriptions_made.append((topic, raw))
        self.callbacks[topic] = callback

    def get_logger(self):
        return FakeLogger()


def hz_match_config(pattern):
    return Config(
        sample_hz=5.0,
        columns=[HzColumn(window=2.0, match=re.compile(pattern))],
    )


def test_match_scan_creates_one_subscription_per_topic():
    node = FakeNode(
        [
            ("/tf", ["tf2_msgs/msg/TFMessage"]),
            ("/tf_static", ["tf2_msgs/msg/TFMessage"]),
            ("/odom", ["nav_msgs/msg/Odometry"]),
        ]
    )
    manager = ColumnManager(node, hz_match_config("^/tf"))
    manager.scan()
    assert node.subscriptions_made == [("/tf", True), ("/tf_static", True)]
    assert [state.name for state in manager.states] == ["tf", "tf_static"]


def test_second_scan_adds_only_the_new_topic():
    node = FakeNode([("/tf", ["tf2_msgs/msg/TFMessage"])])
    manager = ColumnManager(node, hz_match_config("^/tf"))
    manager.scan()
    node.names_and_types.append(("/tf_static", ["tf2_msgs/msg/TFMessage"]))
    added = manager.scan()
    assert added is True
    assert node.subscriptions_made == [("/tf", True), ("/tf_static", True)]
    assert len(manager.states) == 2


def test_rescan_without_new_topics_creates_no_duplicates():
    node = FakeNode([("/tf", ["tf2_msgs/msg/TFMessage"])])
    manager = ColumnManager(node, hz_match_config("^/tf"))
    manager.scan()
    added = manager.scan()
    assert added is False
    assert node.subscriptions_made == [("/tf", True)]


def test_echo_column_subscribes_deserialized_when_topic_present():
    node = FakeNode([("/chatter", ["std_msgs/msg/String"])])
    config = Config(
        sample_hz=5.0,
        columns=[EchoColumn(name="c", topic="/chatter", field="data")],
    )
    manager = ColumnManager(node, config)
    manager.scan()
    assert node.subscriptions_made == [("/chatter", False)]


def test_echo_column_waits_when_topic_absent():
    node = FakeNode([])
    config = Config(
        sample_hz=5.0,
        columns=[EchoColumn(name="c", topic="/chatter", field="data")],
    )
    manager = ColumnManager(node, config)
    manager.scan()
    assert node.subscriptions_made == []


def json_config(subfields, subfield_names):
    column = EchoColumn(
        name="chatter",
        topic="/chatter",
        field="data",
        is_json=True,
        subfields=subfields,
        subfield_names=subfield_names,
    )
    return Config(sample_hz=5.0, columns=[column])


def test_json_subfields_fan_out_from_one_subscription():
    node = FakeNode([("/chatter", ["std_msgs/msg/String"])])
    config = json_config(["reached", "failed"], ["chatter_reached", "chatter_failed"])
    manager = ColumnManager(node, config)
    manager.scan()
    assert node.subscriptions_made == [("/chatter", False)]
    assert [state.name for state in manager.states] == [
        "chatter_reached", "chatter_failed",
    ]
    message = SimpleNamespace(data='{"reached": 3, "failed": 1}')
    node.callbacks["/chatter"](message)
    assert manager.states[0].value == 3
    assert manager.states[1].value == 1


def test_json_without_subfields_expands_on_first_message():
    node = FakeNode([("/chatter", ["std_msgs/msg/String"])])
    manager = ColumnManager(node, json_config(None, None))
    manager.scan()
    assert manager.states == []
    node.callbacks["/chatter"](
        SimpleNamespace(data='{"state": "idle", "reached": 3}')
    )
    assert [state.name for state in manager.states] == [
        "chatter_state", "chatter_reached",
    ]
    assert manager.states[0].value == "idle"


def test_expanded_columns_are_fixed_after_first_message():
    node = FakeNode([("/chatter", ["std_msgs/msg/String"])])
    manager = ColumnManager(node, json_config(None, None))
    manager.scan()
    node.callbacks["/chatter"](SimpleNamespace(data='{"reached": 3}'))
    node.callbacks["/chatter"](SimpleNamespace(data='{"extra": 9}'))
    assert [state.name for state in manager.states] == ["chatter_reached"]
    assert manager.states[0].sample(0.0) == "?"


def test_expander_waits_through_malformed_first_message():
    node = FakeNode([("/chatter", ["std_msgs/msg/String"])])
    manager = ColumnManager(node, json_config(None, None))
    manager.scan()
    node.callbacks["/chatter"](SimpleNamespace(data="not json {"))
    assert manager.states == []
    node.callbacks["/chatter"](SimpleNamespace(data='{"reached": 3}'))
    assert [state.name for state in manager.states] == ["chatter_reached"]


def test_scan_queries_the_graph_once_for_many_pending_columns():
    node = FakeNode([])
    config = Config(
        sample_hz=5.0,
        columns=[
            EchoColumn(name="a", topic="/a", field="x"),
            EchoColumn(name="b", topic="/b", field="x"),
            EchoColumn(name="c", topic="/c", field="x"),
        ],
    )
    manager = ColumnManager(node, config)
    manager.scan()
    assert node.graph_queries == 1
