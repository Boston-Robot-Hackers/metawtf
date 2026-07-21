#!/usr/bin/env python3
"""metawtf.tracer_node: rclpy node that samples echo columns onto stdout CSV.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import time
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node

from metawtf.config import Config, load_config
from metawtf.echo_column import EchoColumnState
from metawtf.msg_type import (
    MessageTypeError,
    TopicNotFoundError,
    resolve_message_type,
)
from metawtf.qos_select import select_qos
from metawtf.sampler import Sampler

CONFIG_FILENAME = "metawtf.yaml"
RESCAN_PERIOD_SEC = 1.0


class TracerNode(Node):
    def __init__(self, config: Config):
        super().__init__("metawtf")
        self.config_columns = config.columns
        self.states = [
            EchoColumnState(column.name, column.field, column.stale_after)
            for column in config.columns
        ]
        self.is_subscribed = [False] * len(config.columns)
        self.sampler = Sampler(self.states)
        for index in range(len(config.columns)):
            self.try_subscribe(index)
        self.create_timer(RESCAN_PERIOD_SEC, self.rescan)
        self.create_timer(1.0 / config.sample_hz, self.on_tick)

    def try_subscribe(self, index: int) -> None:
        if self.is_subscribed[index]:
            return
        column = self.config_columns[index]
        try:
            names_and_types = self.get_topic_names_and_types()
            msg_class = resolve_message_type(
                column.topic, column.type, names_and_types
            )
        except TopicNotFoundError:
            return
        except MessageTypeError as error:
            self.get_logger().error(str(error))
            return
        qos = select_qos(self.get_publishers_info_by_topic(column.topic))
        state = self.states[index]
        self.create_subscription(
            msg_class,
            column.topic,
            lambda msg, state=state: state.on_message(msg, time.monotonic()),
            qos,
        )
        self.is_subscribed[index] = True

    def rescan(self) -> None:
        for index in range(len(self.config_columns)):
            self.try_subscribe(index)

    def on_tick(self) -> None:
        self.sampler.tick(time.monotonic(), datetime.now())


def main(args=None) -> None:
    rclpy.init(args=args)
    config_path = Path.cwd() / CONFIG_FILENAME
    config = load_config(config_path)
    node = TracerNode(config)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
