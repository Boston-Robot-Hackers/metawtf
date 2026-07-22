#!/usr/bin/env python3
"""Tests for metawtf.column_manager.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re

from metawtf.column_manager import ColumnManager
from metawtf.config import Config, EchoColumn, HzColumn


class FakeLogger:
    def error(self, message):
        pass


class FakeNode:
    def __init__(self, names_and_types):
        self.names_and_types = names_and_types
        self.subscriptions_made = []

    def get_topic_names_and_types(self):
        return self.names_and_types

    def get_publishers_info_by_topic(self, topic):
        return []

    def create_subscription(self, msg_class, topic, callback, qos, raw=False):
        self.subscriptions_made.append((topic, raw))

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
