#!/usr/bin/env python3
"""metawtf.msg_type: resolve ROS message types from config or the live graph.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""


class MessageTypeError(Exception):
    """Raised when a message type string or graph lookup cannot be resolved."""


class TopicNotFoundError(Exception):
    """Raised when a topic is not (yet) present in the graph."""


def resolve_type_from_string(type_str: str):
    from rosidl_runtime_py.utilities import get_message

    try:
        return get_message(type_str)
    except (AttributeError, ModuleNotFoundError, ValueError) as error:
        raise MessageTypeError(f"cannot resolve message type {type_str!r}: {error}")


def resolve_type_string_from_graph(topic: str, names_and_types: list) -> str:
    matches = [types for name, types in names_and_types if name == topic]
    if not matches:
        raise TopicNotFoundError(f"topic {topic!r} not found in graph")
    types = matches[0]
    if len(types) != 1:
        raise MessageTypeError(f"topic {topic!r} has multiple types: {types}")
    return types[0]


def resolve_message_type(
    topic: str, configured_type: str | None, names_and_types: list
):
    type_str = configured_type or resolve_type_string_from_graph(
        topic, names_and_types
    )
    return resolve_type_from_string(type_str)
