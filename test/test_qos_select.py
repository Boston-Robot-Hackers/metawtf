#!/usr/bin/env python3
"""Tests for metawtf.qos_select.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from types import SimpleNamespace

import pytest

pytest.importorskip("rclpy.qos")

from metawtf.qos_select import select_qos


def publisher_info(reliability, durability):
    return SimpleNamespace(
        qos_profile=SimpleNamespace(reliability=reliability, durability=durability)
    )


def test_all_reliable_all_transient_local():
    from rclpy.qos import DurabilityPolicy, ReliabilityPolicy

    infos = [
        publisher_info(ReliabilityPolicy.RELIABLE, DurabilityPolicy.TRANSIENT_LOCAL),
        publisher_info(ReliabilityPolicy.RELIABLE, DurabilityPolicy.TRANSIENT_LOCAL),
    ]
    qos = select_qos(infos)
    assert qos.reliability == ReliabilityPolicy.RELIABLE
    assert qos.durability == DurabilityPolicy.TRANSIENT_LOCAL


def test_mixed_reliability_falls_back_to_best_effort():
    from rclpy.qos import DurabilityPolicy, ReliabilityPolicy

    infos = [
        publisher_info(ReliabilityPolicy.RELIABLE, DurabilityPolicy.VOLATILE),
        publisher_info(ReliabilityPolicy.BEST_EFFORT, DurabilityPolicy.VOLATILE),
    ]
    qos = select_qos(infos)
    assert qos.reliability == ReliabilityPolicy.BEST_EFFORT


def test_mixed_durability_falls_back_to_volatile():
    from rclpy.qos import DurabilityPolicy, ReliabilityPolicy

    infos = [
        publisher_info(ReliabilityPolicy.RELIABLE, DurabilityPolicy.TRANSIENT_LOCAL),
        publisher_info(ReliabilityPolicy.RELIABLE, DurabilityPolicy.VOLATILE),
    ]
    qos = select_qos(infos)
    assert qos.durability == DurabilityPolicy.VOLATILE


def test_empty_publisher_list_uses_sensor_data_default():
    from rclpy.qos import qos_profile_sensor_data

    qos = select_qos([])
    assert qos is qos_profile_sensor_data
