#!/usr/bin/env python3
"""Tests for metawtf.field_extract.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from types import SimpleNamespace

import pytest

from metawtf.field_extract import FieldPathError, extract_field


def make_odom(x: float) -> SimpleNamespace:
    position = SimpleNamespace(x=x)
    pose = SimpleNamespace(position=position)
    return SimpleNamespace(pose=SimpleNamespace(pose=pose))


def test_extract_nested_field():
    msg = make_odom(1.5)
    assert extract_field(msg, "pose.pose.position.x") == 1.5


def test_extract_top_level_field():
    msg = SimpleNamespace(data="hello")
    assert extract_field(msg, "data") == "hello"


def test_bad_path_raises():
    msg = make_odom(1.5)
    with pytest.raises(FieldPathError):
        extract_field(msg, "pose.pose.position.bogus")


def test_bad_path_missing_intermediate_raises():
    msg = SimpleNamespace(data="hello")
    with pytest.raises(FieldPathError):
        extract_field(msg, "data.bogus.deeper")
