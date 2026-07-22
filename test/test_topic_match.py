#!/usr/bin/env python3
"""Tests for metawtf.topic_match.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re

from metawtf.topic_match import match_topics

GRAPH = [
    ("/tf", ["tf2_msgs/msg/TFMessage"]),
    ("/tf_static", ["tf2_msgs/msg/TFMessage"]),
    ("/odom", ["nav_msgs/msg/Odometry"]),
    ("/mixed", ["std_msgs/msg/String", "std_msgs/msg/Int32"]),
]


def test_regex_selects_matching_topics_and_types():
    matches = match_topics(re.compile("^/tf"), GRAPH)
    assert matches == [
        ("/tf", "tf2_msgs/msg/TFMessage"),
        ("/tf_static", "tf2_msgs/msg/TFMessage"),
    ]


def test_multi_type_topic_is_skipped():
    matches = match_topics(re.compile("^/mixed"), GRAPH)
    assert matches == []


def test_no_match_returns_empty_list():
    assert match_topics(re.compile("^/camera"), GRAPH) == []


def test_search_semantics_allow_unanchored_patterns():
    matches = match_topics(re.compile("odom"), GRAPH)
    assert matches == [("/odom", "nav_msgs/msg/Odometry")]
