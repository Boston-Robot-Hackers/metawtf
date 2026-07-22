#!/usr/bin/env python3
"""metawtf.topic_match: select graph topics by regex for hz columns.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import logging
import re

logger = logging.getLogger(__name__)


def match_topics(pattern: re.Pattern, names_and_types: list) -> list:
    """Return (topic, type) pairs whose name matches pattern.

    Multi-type topics are skipped with a warning rather than guessed at, since
    a wrong type silently delivers zero messages. No match yields an empty list.
    """
    matches = []
    for name, types in names_and_types:
        if pattern.search(name) is None:
            continue
        if len(types) != 1:
            logger.warning("skipping multi-type topic %r: %s", name, types)
            continue
        matches.append((name, types[0]))
    return matches
