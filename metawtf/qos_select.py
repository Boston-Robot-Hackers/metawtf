#!/usr/bin/env python3
"""metawtf.qos_select: graph-checked QoS auto-selection for arbitrary topics.

Port of ros2cli's `choose_qos`, without CLI args: RELIABLE only if every
publisher offers RELIABLE else BEST_EFFORT; TRANSIENT_LOCAL only if every
publisher offers it else VOLATILE. Wrong QoS silently delivers zero messages,
so this stays graph-checked rather than hardcoded.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""


def select_qos(publishers_info: list):
    from rclpy.qos import (
        DurabilityPolicy,
        HistoryPolicy,
        QoSProfile,
        ReliabilityPolicy,
        qos_profile_sensor_data,
    )

    if not publishers_info:
        return qos_profile_sensor_data

    is_all_reliable = all(
        info.qos_profile.reliability == ReliabilityPolicy.RELIABLE
        for info in publishers_info
    )
    is_all_transient_local = all(
        info.qos_profile.durability == DurabilityPolicy.TRANSIENT_LOCAL
        for info in publishers_info
    )
    return QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=10,
        reliability=(
            ReliabilityPolicy.RELIABLE
            if is_all_reliable
            else ReliabilityPolicy.BEST_EFFORT
        ),
        durability=(
            DurabilityPolicy.TRANSIENT_LOCAL
            if is_all_transient_local
            else DurabilityPolicy.VOLATILE
        ),
    )
