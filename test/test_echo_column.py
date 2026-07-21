#!/usr/bin/env python3
"""Tests for metawtf.echo_column.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from types import SimpleNamespace

from metawtf.echo_column import EchoColumnState


def test_sample_before_any_message_is_none():
    state = EchoColumnState("odom_x", "data", None)
    assert state.sample(0.0) is None


def test_sample_after_message_returns_formatted_float():
    state = EchoColumnState("odom_x", "data", None)
    state.on_message(SimpleNamespace(data=1.23456789), now=10.0)
    assert state.sample(10.1) == "1.23457"


def test_sample_non_float_uses_str():
    state = EchoColumnState("label", "data", None)
    state.on_message(SimpleNamespace(data="hello"), now=10.0)
    assert state.sample(10.1) == "hello"


def test_sample_stale_returns_none():
    state = EchoColumnState("odom_x", "data", stale_after=2.0)
    state.on_message(SimpleNamespace(data=1.0), now=10.0)
    assert state.sample(13.0) is None


def test_sample_within_stale_window_returns_value():
    state = EchoColumnState("odom_x", "data", stale_after=2.0)
    state.on_message(SimpleNamespace(data=1.0), now=10.0)
    assert state.sample(11.5) == "1"
