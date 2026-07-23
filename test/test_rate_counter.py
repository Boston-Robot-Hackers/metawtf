#!/usr/bin/env python3
"""Tests for metawtf.rate_counter.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import pytest

from metawtf.rate_counter import RateCounter


def test_steady_stream_reads_expected_rate():
    counter = RateCounter(window=2.0)
    now = 0.0
    for _ in range(21):
        counter.record(now)
        now += 0.1
    assert counter.rate(2.0) == pytest.approx(10.0)


def test_sparse_startup_is_not_underreported():
    counter = RateCounter(window=2.0)
    for arrival in (0.0, 0.1, 0.2):
        counter.record(arrival)
    assert counter.rate(0.2) == pytest.approx(10.0)


def test_single_message_returns_none():
    counter = RateCounter(window=2.0)
    counter.record(0.0)
    assert counter.rate(0.0) is None


def test_no_messages_returns_none():
    counter = RateCounter(window=2.0)
    assert counter.rate(1.0) is None


def test_old_entries_are_pruned():
    counter = RateCounter(window=1.0)
    counter.record(0.0)
    counter.record(0.1)
    counter.record(5.0)
    counter.record(5.1)
    assert counter.rate(5.1) == pytest.approx(10.0)


def test_simultaneous_arrivals_return_none():
    counter = RateCounter(window=2.0)
    counter.record(1.0)
    counter.record(1.0)
    assert counter.rate(1.0) is None


def test_record_prunes_without_rate_calls():
    # Sampling can pause while messages keep arriving; record must keep the
    # deque bounded even when rate() is never called.
    counter = RateCounter(window=1.0)
    now = 0.0
    for _ in range(1000):
        counter.record(now)
        now += 0.01
    assert len(counter.arrivals) <= 101
