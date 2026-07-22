#!/usr/bin/env python3
"""metawtf.tracer_node: rclpy node that samples echo columns onto stdout CSV.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import sys
import termios
import threading
import time
import tty
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from metawtf.column_manager import ColumnManager
from metawtf.config import Config, load_config
from metawtf.sampler import Sampler

CONFIG_FILENAME = "metawtf.yaml"
RESCAN_PERIOD_SEC = 1.0


class TracerNode(Node):
    def __init__(self, config: Config):
        super().__init__("metawtf")
        self.manager = ColumnManager(self, config)
        self.states = self.manager.states
        self.sampler = Sampler(self.states, config.time)
        self.manager.scan()
        self.create_timer(RESCAN_PERIOD_SEC, self.manager.scan)
        self.create_timer(1.0 / config.sample_hz, self.on_tick)

    def on_tick(self) -> None:
        self.sampler.tick(time.monotonic(), datetime.now())


def default_config_path() -> Path:
    return Path.cwd() / CONFIG_FILENAME


def wait_for_quit(stream, on_quit) -> None:
    # Quit on a bare 'q' keypress (no Enter needed) or EOF. Runs on a daemon
    # thread; the terminal is put in cbreak mode so single chars arrive live.
    while True:
        char = stream.read(1)
        if char == "" or char.lower() == "q":
            break
    on_quit()


def start_quit_watcher(on_quit):
    # Returns a restore callable, or None when stdin is not an interactive tty
    # (e.g. piped input) — in that case only Ctrl-C stops the run.
    if sys.stdin is None or not sys.stdin.isatty():
        return None
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    print("metawtf running — press q or Ctrl-C to quit.", file=sys.stderr)
    thread = threading.Thread(
        target=wait_for_quit, args=(sys.stdin, on_quit), daemon=True
    )
    thread.start()
    return lambda: termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def spin_until_quit(node) -> None:
    stop = threading.Event()
    restore = start_quit_watcher(stop.set)
    try:
        while rclpy.ok() and not stop.is_set():
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        if restore is not None:
            restore()


def main(args=None) -> None:
    rclpy.init(args=args)
    config = load_config(default_config_path())
    node = TracerNode(config)
    try:
        spin_until_quit(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        print("metawtf stopped.", file=sys.stderr)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
