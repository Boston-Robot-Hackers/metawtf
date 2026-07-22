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

HELP_TEXT = """\
metawtf — sample ROS2 topic values into CSV columns

usage: metawtf [-h] [-f config.yaml]
  -h   show this help and exit
  -f   read config from the given yaml (default: ./metawtf.yaml)

keys while running:
  space  pause / resume output
  h      show this help
  q      quit (Ctrl-C also works)
"""


class TracerNode(Node):
    def __init__(self, config: Config):
        super().__init__("metawtf")
        self.manager = ColumnManager(self, config)
        self.states = self.manager.states
        self.sampler = Sampler(self.states, config.time)
        self.is_paused = False
        self.manager.scan()
        self.create_timer(RESCAN_PERIOD_SEC, self.manager.scan)
        self.create_timer(1.0 / config.sample_hz, self.on_tick)

    def toggle_pause(self) -> None:
        # Subscriptions keep running while paused; only row output stops, so the
        # first row after resuming shows current values, not a backlog.
        self.is_paused = not self.is_paused
        print("metawtf paused." if self.is_paused else "metawtf resumed.",
              file=sys.stderr)

    def on_tick(self) -> None:
        if self.is_paused:
            return
        self.sampler.tick(time.monotonic(), datetime.now())


def default_config_path() -> Path:
    return Path.cwd() / CONFIG_FILENAME


def print_help() -> None:
    print(HELP_TEXT, file=sys.stderr)


def parse_cli(argv: list[str]) -> Path:
    # Deliberately minimal: only -h and -f, no argparse.
    config_path = default_config_path()
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "-h":
            print_help()
            raise SystemExit(0)
        if arg == "-f" and args:
            config_path = Path(args.pop(0))
            continue
        raise SystemExit(f"metawtf: bad argument {arg!r}\n\n{HELP_TEXT}")
    return config_path


def watch_keys(stream, on_quit, on_pause, on_help=print_help) -> None:
    # Quit on a bare 'q' keypress (no Enter needed) or EOF; toggle pause on
    # space; show help on 'h'. Runs on a daemon thread; the terminal is in
    # cbreak mode so single chars arrive live.
    while True:
        char = stream.read(1)
        if char == "" or char.lower() == "q":
            break
        if char == " ":
            on_pause()
        if char.lower() == "h":
            on_help()
    on_quit()


def start_key_watcher(on_quit, on_pause):
    # Returns a restore callable, or None when stdin is not an interactive tty
    # (e.g. piped input) — in that case only Ctrl-C stops the run.
    if sys.stdin is None or not sys.stdin.isatty():
        return None
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    print("metawtf running — space pauses, h help, q or Ctrl-C quits.",
          file=sys.stderr)
    thread = threading.Thread(
        target=watch_keys, args=(sys.stdin, on_quit, on_pause), daemon=True
    )
    thread.start()
    return lambda: termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def spin_until_quit(node) -> None:
    stop = threading.Event()
    restore = start_key_watcher(stop.set, node.toggle_pause)
    try:
        while rclpy.ok() and not stop.is_set():
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        if restore is not None:
            restore()


def main(args=None) -> None:
    config_path = parse_cli(sys.argv[1:])
    rclpy.init(args=args)
    config = load_config(config_path)
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
