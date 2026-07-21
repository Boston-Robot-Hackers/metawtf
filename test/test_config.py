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


def test_default_name_from_topic_and_field():
    config = load(
        """
        columns:
          - metric: echo
            topic: /odom
            field: pose.pose.position.x
        """
    )
    assert config.columns[0].name == "odom_x"


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
        load("columns:\n  - metric: hz\n    topic: /odom\n    field: x\n")


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
