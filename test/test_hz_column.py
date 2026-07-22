#!/usr/bin/env python3
"""Tests for metawtf.hz_column.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from metawtf.hz_column import HzColumnState


def test_from_topic_derives_sanitized_name():
    state = HzColumnState.from_topic("/tf_static", window=2.0)
    assert state.name == "tf_static"


def test_from_topic_replaces_inner_slashes():
    state = HzColumnState.from_topic("/robot/scan", window=2.0)
    assert state.name == "robot_scan"


def test_on_message_records_arrival_and_ignores_payload():
    state = HzColumnState("tf", window=2.0)
    for arrival in (0.0, 0.1, 0.2):
        state.on_message(b"serialized-bytes-ignored", now=arrival)
    assert state.sample(0.2) == "10.00"


def test_sample_before_two_messages_is_none():
    state = HzColumnState("tf", window=2.0)
    state.on_message(b"x", now=0.0)
    assert state.sample(0.0) is None
