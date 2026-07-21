#!/usr/bin/env python3
"""Tests for metawtf.tracer_node.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from types import SimpleNamespace

import pytest

rclpy = pytest.importorskip("rclpy")

from metawtf.config import Config, EchoColumn
from metawtf.tracer_node import TracerNode


@pytest.fixture(autouse=True)
def ros_context():
    rclpy.init()
    yield
    rclpy.shutdown()


def test_node_constructs_and_destroys_with_no_publishers():
    config = Config(
        sample_hz=5.0,
        columns=[EchoColumn(name="x", topic="/nope", field="data")],
    )
    node = TracerNode(config)
    node.destroy_node()


def test_on_message_updates_echo_state():
    config = Config(
        sample_hz=5.0,
        columns=[EchoColumn(name="x", topic="/nope", field="data")],
    )
    node = TracerNode(config)
    node.states[0].on_message(SimpleNamespace(data=1.0), now=0.0)
    assert node.states[0].sample(0.0) == "1"
    node.destroy_node()
