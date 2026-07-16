#!/usr/bin/env python3
# frontier_algorithm.py — default frontier exploration algorithm
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from dome_nav.explore_context import ExplorationContext, GoalDecision
from dome_nav.frontier_params import (
    FrontierParams,
    declare_frontier_params,
    merge_tuning,
)
from dome_nav.frontier_explorer import (
    find_frontier_clusters,
    nudge_toward_robot,
    pick_best_frontier,
    frontier_diag,
)


class FrontierAlgorithm:
    # Default exploration algorithm. Wraps the pure functions in
    # frontier_explorer.py behind the ExplorationAlgorithm protocol. Owns its own
    # frontier tuning (FrontierParams); the manager node no longer declares or
    # carries frontier params. next_goal merges the shared params from the context
    # with these to feed the pure functions.

    def __init__(self, frontier_params: FrontierParams | None = None):
        self.latest_clusters: list[list[int]] = []
        self.latest_diag: dict | None = None
        self.frontier_params = frontier_params or FrontierParams()

    def declare_params(self, node):
        # Node calls this once at construction. The frontier algorithm declares its
        # own ROS params in the node's namespace (see declare_frontier_params) so
        # they stay yaml/launch settable without leaking frontier names into the node.
        self.frontier_params = declare_frontier_params(node)

    def next_goal(self, ctx: ExplorationContext) -> GoalDecision:
        tuning = merge_tuning(ctx.params, self.frontier_params)
        clusters = find_frontier_clusters(
            ctx.map_data, ctx.map_info, tuning.frontier_buffer_cells
        )
        self.latest_clusters = clusters
        target = pick_best_frontier(
            clusters, ctx.map_info, ctx.robot_xy, tuning,
            blacklist=ctx.blacklist, start_xy=ctx.start_xy,
        )
        if target is None:
            self.latest_diag = frontier_diag(
                clusters,
                ctx.map_info,
                ctx.robot_xy,
                tuning.min_frontier_size,
                tuning.min_frontier_dist,
                tuning.max_frontier_dist,
            )
            # No raw clusters at all -> the map is fully explored; the frontier
            # algorithm owns this done-condition. Clusters present but none survive
            # filtering/blacklisting -> blocked this tick, not finished.
            if not clusters:
                return GoalDecision.done()
            return GoalDecision.blocked()
        self.latest_diag = None
        goal = nudge_toward_robot(target, ctx.robot_xy, tuning.goal_inset_m)
        return GoalDecision.new_goal(goal)
