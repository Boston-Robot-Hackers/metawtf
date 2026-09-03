#!/usr/bin/env python3
"""Tests for metawtf.json_column.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from types import SimpleNamespace

from metawtf.json_column import JsonEchoColumnState


def msg(data):
    return SimpleNamespace(data=data)


def test_selects_scalar_from_json_string():
    state = JsonEchoColumnState("reached", "data", "reached", None)
    state.on_message(msg('{"state": "idle", "reached": 3}'), now=1.0)
    assert state.sample(1.1) == "3"


def test_nested_key():
    state = JsonEchoColumnState("count", "data", "payload.count", None)
    state.on_message(msg('{"payload": {"count": 7}}'), now=1.0)
    assert state.sample(1.1) == "7"


def test_empty_before_any_message():
    state = JsonEchoColumnState("reached", "data", "reached", None)
    assert state.sample(0.0) is None


def test_malformed_json_shows_question_mark():
    state = JsonEchoColumnState("reached", "data", "reached", None)
    state.on_message(msg("not json {"), now=1.0)
    assert state.sample(1.1) == "?"


def test_missing_key_shows_question_mark():
    state = JsonEchoColumnState("reached", "data", "reached", None)
    state.on_message(msg('{"state": "idle"}'), now=1.0)
    assert state.sample(1.1) == "?"


def test_non_scalar_value_shows_question_mark():
    state = JsonEchoColumnState("payload", "data", "payload", None)
    state.on_message(msg('{"payload": {"count": 7}}'), now=1.0)
    assert state.sample(1.1) == "?"


def test_bad_field_path_shows_question_mark():
    state = JsonEchoColumnState("reached", "nope", "reached", None)
    state.on_message(msg('{"reached": 3}'), now=1.0)
    assert state.sample(1.1) == "?"


def test_recovers_after_good_message():
    state = JsonEchoColumnState("reached", "data", "reached", None)
    state.on_message(msg("garbage"), now=1.0)
    assert state.sample(1.1) == "?"
    state.on_message(msg('{"reached": 5}'), now=2.0)
    assert state.sample(2.1) == "5"


def test_indexed_outer_field_works_for_free():
    # `field` here is the F11 path into the message, not the JSON key -- proof
    # that json_column needed no change to gain indexing.
    state = JsonEchoColumnState("count", "frames[0].data", "payload.count", None)
    outer = SimpleNamespace(frames=[SimpleNamespace(data='{"payload": {"count": 5}}')])
    state.on_message(outer, now=1.0)
    assert state.sample(1.1) == "5"
