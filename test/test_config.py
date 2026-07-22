#!/usr/bin/env python3
"""Tests for metawtf.config.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import pytest
import yaml

from metawtf.config import ConfigError, parse_config


def load(yaml_text: str):
    return parse_config(yaml.safe_load(yaml_text))


def test_minimal_valid_config_uses_default_sample_hz():
    config = load(
        """
        columns:
          - name: odom_x
            metric: echo
            topic: /odom
            field: pose.pose.position.x
        """
    )
    assert config.sample_hz == 5.0
    assert config.columns[0].name == "odom_x"
    assert config.columns[0].topic == "/odom"
    assert config.columns[0].field == "pose.pose.position.x"
    assert config.columns[0].type is None
    assert config.columns[0].stale_after is None


def test_explicit_sample_hz_and_optional_fields():
    config = load(
        """
        sample_hz: 10
        columns:
          - metric: echo
            topic: /odom
            type: nav_msgs/msg/Odometry
            field: pose.pose.position.x
            stale_after: 2.0
        """
    )
    assert config.sample_hz == 10.0
    assert config.columns[0].type == "nav_msgs/msg/Odometry"
    assert config.columns[0].stale_after == 2.0


def test_default_name_is_sanitized_topic():
    config = load(
        """
        columns:
          - metric: echo
            topic: /robot/odom
            field: pose.pose.position.x
        """
    )
    assert config.columns[0].name == "robot_odom"


def test_missing_field_raises():
    with pytest.raises(ConfigError):
        load("columns:\n  - metric: echo\n    topic: /odom\n")


def test_non_numeric_sample_hz_raises():
    with pytest.raises(ConfigError):
        load(
            "sample_hz: fast\ncolumns:\n  - metric: echo\n    topic: /odom\n"
            "    field: x\n"
        )


def test_zero_sample_hz_raises():
    with pytest.raises(ConfigError):
        load(
            "sample_hz: 0\ncolumns:\n  - metric: echo\n    topic: /odom\n"
            "    field: x\n"
        )


def test_unknown_top_level_key_raises():
    with pytest.raises(ConfigError):
        load("columns: []\nbogus: 1\n")


def test_unknown_metric_raises():
    with pytest.raises(ConfigError):
        load("columns:\n  - metric: bogus\n    topic: /odom\n    field: x\n")


def test_unknown_column_key_raises():
    with pytest.raises(ConfigError):
        load(
            "columns:\n  - metric: echo\n    topic: /odom\n    field: x\n"
            "    bogus: 1\n"
        )


def test_invalid_stale_after_raises():
    with pytest.raises(ConfigError):
        load(
            "columns:\n  - metric: echo\n    topic: /odom\n    field: x\n"
            "    stale_after: -1\n"
        )


def test_empty_columns_list_raises():
    with pytest.raises(ConfigError):
        load("columns: []\n")


def test_hz_single_topic_parses_with_default_window():
    config = load(
        """
        columns:
          - metric: hz
            topic: /tf
        """
    )
    column = config.columns[0]
    assert column.topic == "/tf"
    assert column.match is None
    assert column.name == "tf"
    assert column.window == 2.0


def test_hz_match_compiles_regex_and_has_no_name():
    config = load(
        """
        columns:
          - metric: hz
            match: "^/tf"
            window: 3.0
        """
    )
    column = config.columns[0]
    assert column.topic is None
    assert column.match.pattern == "^/tf"
    assert column.name is None
    assert column.window == 3.0


def test_hz_mixed_with_echo_columns():
    config = load(
        """
        columns:
          - metric: echo
            topic: /odom
            field: pose.pose.position.x
          - metric: hz
            topic: /chatter
        """
    )
    assert config.columns[0].field == "pose.pose.position.x"
    assert config.columns[1].topic == "/chatter"


def test_hz_topic_and_match_together_raises():
    with pytest.raises(ConfigError):
        load("columns:\n  - metric: hz\n    topic: /tf\n    match: '^/tf'\n")


def test_hz_neither_topic_nor_match_raises():
    with pytest.raises(ConfigError):
        load("columns:\n  - metric: hz\n")


def test_hz_bad_regex_raises():
    with pytest.raises(ConfigError):
        load("columns:\n  - metric: hz\n    match: '['\n")


def test_hz_window_below_sample_period_raises():
    with pytest.raises(ConfigError):
        load(
            "sample_hz: 5.0\ncolumns:\n  - metric: hz\n    topic: /tf\n"
            "    window: 0.1\n"
        )


def test_hz_name_with_match_raises():
    with pytest.raises(ConfigError):
        load("columns:\n  - metric: hz\n    match: '^/tf'\n    name: foo\n")


def test_hz_unknown_key_raises():
    with pytest.raises(ConfigError):
        load("columns:\n  - metric: hz\n    topic: /tf\n    bogus: 1\n")


def test_width_parses_on_echo_and_hz_columns():
    config = load(
        """
        columns:
          - metric: echo
            topic: /odom
            field: pose.pose.position.x
            width: 10
          - metric: hz
            topic: /tf
            width: 6
        """
    )
    assert config.columns[0].width == 10
    assert config.columns[1].width == 6


def test_width_defaults_to_none():
    config = load(
        "columns:\n  - metric: echo\n    topic: /odom\n    field: x\n"
    )
    assert config.columns[0].width is None


def test_non_integer_width_raises():
    with pytest.raises(ConfigError):
        load(
            "columns:\n  - metric: echo\n    topic: /odom\n    field: x\n"
            "    width: 3.5\n"
        )


def test_zero_width_raises():
    with pytest.raises(ConfigError):
        load(
            "columns:\n  - metric: echo\n    topic: /odom\n    field: x\n"
            "    width: 0\n"
        )


def test_time_defaults_when_absent():
    config = load("columns:\n  - metric: echo\n    topic: /odom\n    field: x\n")
    assert config.time.format is None
    assert config.time.width is None


def test_time_format_and_width_parse():
    config = load(
        """
        time:
          format: "%H:%M:%S"
          width: 12
        columns:
          - metric: echo
            topic: /odom
            field: x
        """
    )
    assert config.time.format == "%H:%M:%S"
    assert config.time.width == 12


def test_time_unknown_key_raises():
    with pytest.raises(ConfigError):
        load(
            "time:\n  bogus: 1\ncolumns:\n  - metric: echo\n"
            "    topic: /odom\n    field: x\n"
        )
