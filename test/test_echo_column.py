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
    assert state.sample(10.1) == "1.23"


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
    assert state.sample(11.5) == "1.00"


def test_bad_field_path_shows_question_mark_not_crash():
    state = EchoColumnState("x", "nope.missing", None)
    state.on_message(SimpleNamespace(data=1.0), now=10.0)
    assert state.sample(10.1) == "?"


def test_recovers_to_value_after_a_good_message():
    state = EchoColumnState("x", "data", None)
    state.on_message(SimpleNamespace(other=1.0), now=10.0)  # no 'data' -> ?
    assert state.sample(10.1) == "?"
    state.on_message(SimpleNamespace(data=2.0), now=11.0)
    assert state.sample(11.1) == "2.00"


def detections(count: int) -> SimpleNamespace:
    return SimpleNamespace(
        detections=[SimpleNamespace(id=float(n)) for n in range(count)]
    )


def test_indexed_path_goes_question_mark_on_an_empty_array():
    state = EchoColumnState("first", "detections[0].id", None)
    state.on_message(detections(2), now=10.0)
    assert state.sample(10.1) == "0.00"
    state.on_message(detections(0), now=11.0)
    assert state.sample(11.1) == "?"
    state.on_message(detections(2), now=12.0)
    assert state.sample(12.1) == "0.00"


def test_length_path_reads_zero_on_an_empty_array():
    # The asymmetry with the indexed path above is the point: a count must stay
    # a value across an empty frame, which is why length answers "how many".
    state = EchoColumnState("ntrk", "detections.#", None)
    state.on_message(detections(2), now=10.0)
    assert state.sample(10.1) == "2"
    state.on_message(detections(0), now=11.0)
    assert state.sample(11.1) == "0"
    state.on_message(detections(2), now=12.0)
    assert state.sample(12.1) == "2"
