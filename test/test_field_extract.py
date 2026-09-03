#!/usr/bin/env python3
"""Tests for metawtf.field_extract.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import re
from types import SimpleNamespace

import pytest

from metawtf.field_extract import FieldPathError, extract_field, parse_path


def make_odom(x: float) -> SimpleNamespace:
    position = SimpleNamespace(x=x)
    pose = SimpleNamespace(position=position)
    return SimpleNamespace(pose=SimpleNamespace(pose=pose))


def make_detections(*ids) -> SimpleNamespace:
    return SimpleNamespace(detections=[SimpleNamespace(id=one) for one in ids])


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


@pytest.mark.parametrize(
    "path,expected",
    [
        ("data", [("data", None, False)]),
        ("pose.position.x", [
            ("pose", None, False),
            ("position", None, False),
            ("x", None, False),
        ]),
        ("detections[0].id", [
            ("detections", 0, False),
            ("id", None, False),
        ]),
        ("detections[-1].id", [
            ("detections", -1, False),
            ("id", None, False),
        ]),
        ("detections[0].results[2].score", [
            ("detections", 0, False),
            ("results", 2, False),
            ("score", None, False),
        ]),
        ("detections.#", [
            ("detections", None, False),
            (None, None, True),
        ]),
        ("#", [(None, None, True)]),
    ],
)
def test_parse_path_shapes(path, expected):
    parsed = [(seg.name, seg.index, seg.is_length) for seg in parse_path(path)]
    assert parsed == expected


@pytest.mark.parametrize(
    "path,offender",
    [
        ("detections[0.id", "detections[0"),
        ("detections[].id", "detections[]"),
        ("detections[a].id", "detections[a]"),
        ("detections].id", "detections]"),
        ("[0].id", "[0]"),
    ],
)
def test_parse_path_malformed_brackets_name_the_segment(path, offender):
    with pytest.raises(FieldPathError, match=re.escape(repr(offender))):
        parse_path(path)


def test_index_reads_element():
    msg = make_detections("a", "b", "c")
    assert extract_field(msg, "detections[0].id") == "a"


def test_negative_index_counts_from_end():
    msg = make_detections("a", "b", "c")
    assert extract_field(msg, "detections[-1].id") == "c"


def test_index_out_of_range_raises():
    msg = make_detections("a")
    with pytest.raises(FieldPathError, match="out of range"):
        extract_field(msg, "detections[3].id")


def test_indexing_a_scalar_raises():
    msg = SimpleNamespace(count=7)
    with pytest.raises(FieldPathError, match="not indexable"):
        extract_field(msg, "count[0]")


def test_unindexed_segment_returns_the_sequence():
    msg = make_detections("a", "b")
    assert extract_field(msg, "detections") == msg.detections


def test_length_returns_count():
    msg = make_detections("a", "b", "c")
    assert extract_field(msg, "detections.#") == 3


def test_length_of_empty_array_is_zero():
    # The case that matters for a track-count column: an empty frame must read
    # 0, not "?" -- otherwise the dashboard cannot tell empty from broken.
    msg = make_detections()
    assert extract_field(msg, "detections.#") == 0


def test_non_final_length_raises_at_parse_time():
    with pytest.raises(FieldPathError, match="final segment"):
        parse_path("detections.#.id")


def test_indexed_length_raises_at_parse_time():
    with pytest.raises(FieldPathError, match="no index"):
        parse_path("detections.#[0]")


def test_length_of_scalar_raises():
    msg = SimpleNamespace(count=7)
    with pytest.raises(FieldPathError, match="has no length"):
        extract_field(msg, "count.#")
