#!/usr/bin/env python3
"""Tests for metawtf.tracer_node.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

from types import SimpleNamespace

import pytest

rclpy = pytest.importorskip("rclpy")

import io
import sys
from pathlib import Path

from metawtf.config import Config, EchoColumn
from metawtf.tracer_node import (
    TracerNode,
    default_config_path,
    main,
    parse_cli,
    watch_keys,
)


def noop():
    pass


def test_watch_keys_stops_on_q():
    quits = []
    watch_keys(io.StringIO("q"), lambda: quits.append(True), noop)
    assert quits == [True]


def test_watch_keys_stops_on_eof():
    quits = []
    watch_keys(io.StringIO(""), lambda: quits.append(True), noop)
    assert quits == [True]


def test_watch_keys_space_toggles_pause_without_quitting():
    quits = []
    pauses = []
    watch_keys(
        io.StringIO("  q"),  # two spaces then q
        lambda: quits.append(True),
        lambda: pauses.append(True),
    )
    assert pauses == [True, True]
    assert quits == [True]


def test_watch_keys_h_shows_help_without_quitting():
    quits = []
    helps = []
    watch_keys(
        io.StringIO("hq"),
        lambda: quits.append(True),
        noop,
        on_help=lambda: helps.append(True),
    )
    assert helps == [True]
    assert quits == [True]


def test_parse_cli_default_is_cwd_config():
    assert parse_cli([]) == Path.cwd() / "metawtf.conf"


def test_parse_cli_f_overrides_config_path():
    assert parse_cli(["-f", "other.conf"]) == Path("other.conf")


def test_parse_cli_h_prints_help_and_exits(capsys):
    with pytest.raises(SystemExit) as excinfo:
        parse_cli(["-h"])
    assert excinfo.value.code == 0
    assert "usage: metawtf" in capsys.readouterr().err


def test_parse_cli_unknown_argument_exits_nonzero():
    with pytest.raises(SystemExit) as excinfo:
        parse_cli(["--bogus"])
    assert excinfo.value.code != 0


def test_parse_cli_f_without_value_exits_nonzero():
    with pytest.raises(SystemExit):
        parse_cli(["-f"])


@pytest.fixture(autouse=True)
def ros_context():
    rclpy.init()
    yield
    rclpy.shutdown()


def test_config_path_is_current_directory():
    assert default_config_path() == Path.cwd() / "metawtf.conf"


def test_node_constructs_and_destroys_with_no_publishers():
    config = Config(
        sample_hz=5.0,
        columns=[EchoColumn(name="x", topic="/nope", field="data")],
    )
    node = TracerNode(config)
    node.destroy_node()


def test_on_message_updates_echo_state():
    config = Config(
        sample_hz=5.0,
        columns=[EchoColumn(name="x", topic="/nope", field="data")],
    )
    node = TracerNode(config)
    node.states[0].on_message(SimpleNamespace(data=1.0), now=0.0)
    assert node.states[0].sample(0.0) == "1.00"
    node.destroy_node()


def test_main_exits_cleanly_on_missing_config(tmp_path, monkeypatch):
    missing = tmp_path / "nope.conf"
    monkeypatch.setattr(sys, "argv", ["metawtf", "-f", str(missing)])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code != 0
    assert "cannot read config" in str(excinfo.value)
