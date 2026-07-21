#!/usr/bin/env python3
"""Tests for metawtf.msg_type.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import pytest

from metawtf.msg_type import (
    MessageTypeError,
    TopicNotFoundError,
    resolve_type_string_from_graph,
)


def test_graph_lookup_finds_single_type():
    names_and_types = [
        ("/odom", ["nav_msgs/msg/Odometry"]),
        ("/tf", ["tf2_msgs/msg/TFMessage"]),
    ]
    result = resolve_type_string_from_graph("/odom", names_and_types)
    assert result == "nav_msgs/msg/Odometry"


def test_graph_lookup_multi_type_raises():
    names_and_types = [
        ("/odom", ["nav_msgs/msg/Odometry", "std_msgs/msg/String"]),
    ]
    with pytest.raises(MessageTypeError):
        resolve_type_string_from_graph("/odom", names_and_types)


def test_graph_lookup_absent_topic_raises_not_found():
    with pytest.raises(TopicNotFoundError):
        resolve_type_string_from_graph("/missing", [])


def test_resolve_from_string_finds_class():
    pytest.importorskip("rosidl_runtime_py")
    from metawtf.msg_type import resolve_type_from_string

    msg_class = resolve_type_from_string("std_msgs/msg/String")
    assert msg_class.__name__ == "String"


def test_resolve_from_string_bogus_type_raises():
    pytest.importorskip("rosidl_runtime_py")
    from metawtf.msg_type import resolve_type_from_string

    with pytest.raises(MessageTypeError):
        resolve_type_from_string("not/a/real/type")
