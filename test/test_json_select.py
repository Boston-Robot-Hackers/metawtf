#!/usr/bin/env python3
"""Tests for metawtf.json_select.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import pytest

from metawtf.json_select import JsonSelectError, select_json_value

DOC = {
    "state": "idle",
    "reached": 3,
    "ratio": 0.5,
    "done": True,
    "payload": {"count": 7},
    "list": [1, 2],
    "nothing": None,
}


def test_flat_scalar_keys():
    assert select_json_value(DOC, "state") == "idle"
    assert select_json_value(DOC, "reached") == 3
    assert select_json_value(DOC, "ratio") == 0.5
    assert select_json_value(DOC, "done") is True


def test_nested_dotted_key():
    assert select_json_value(DOC, "payload.count") == 7


def test_missing_key_raises():
    with pytest.raises(JsonSelectError):
        select_json_value(DOC, "missing")


def test_missing_nested_key_raises():
    with pytest.raises(JsonSelectError):
        select_json_value(DOC, "payload.nope")


def test_object_value_is_not_scalar():
    with pytest.raises(JsonSelectError):
        select_json_value(DOC, "payload")


def test_array_value_is_not_scalar():
    with pytest.raises(JsonSelectError):
        select_json_value(DOC, "list")


def test_null_value_is_not_scalar():
    with pytest.raises(JsonSelectError):
        select_json_value(DOC, "nothing")
