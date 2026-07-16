#!/usr/bin/env python3
# frontier_algorithm.py — default frontier exploration algorithm
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from visualization_msgs.msg import MarkerArray

from dome_nav.explore_context import (
    ExplorationContext,
    GoalDecision,
    RenderContext,
)
from dome_nav.explore_diagnostics import (
    format_cluster_summary,
    format_frontier_exhaustion,
)
from dome_nav.explore_markers import build_explore_markers
from dome_nav.frontier_explorer import (
    find_frontier_clusters,
    nudge_toward_robot,
    pick_best_frontier,
    frontier_diag,
)

NO_FRONTIER_PATIENCE = 14


class FrontierAlgorithm:
    # Default exploration algorithm. Wraps the pure functions in
    # frontier_explorer.py behind the ExplorationAlgorithm protocol. It keeps its
    # own frontier state (latest_clusters/latest_diag) for the optional
    # visualization and diagnostics hooks; that state is no longer part of the
    # protocol the node depends on.

    def __init__(self):
        self.latest_clusters: list[list[int]] = []
        self.latest_diag: dict | None = None

    def next_goal(self, ctx: ExplorationContext) -> GoalDecision:
        clusters = find_frontier_clusters(
            ctx.map_data, ctx.map_info, ctx.params.frontier_buffer_cells
        )
        self.latest_clusters = clusters
        target = pick_best_frontier(
            clusters, ctx.map_info, ctx.robot_xy, ctx.params,
            blacklist=ctx.blacklist, start_xy=ctx.start_xy,
        )
        if target is None:
            self.latest_diag = frontier_diag(
                clusters,
                ctx.map_info,
                ctx.robot_xy,
                ctx.params.min_frontier_size,
                ctx.params.min_frontier_dist,
                ctx.params.max_frontier_dist,
            )
            # No raw clusters at all -> the map is fully explored; the frontier
            # algorithm owns this done-condition. Clusters present but none survive
            # filtering/blacklisting -> blocked this tick, not finished.
            if not clusters:
                return GoalDecision.done()
            return GoalDecision.blocked()
        self.latest_diag = None
        goal = nudge_toward_robot(target, ctx.robot_xy, ctx.params.goal_inset_m)
        return GoalDecision.new_goal(goal)

    def render_markers(self, rc: RenderContext) -> MarkerArray:
        # Frontier visualization: the yellow frontier points plus the general
        # blacklist and goal markers. The node publishes whatever we return here.
        return build_explore_markers(
            now=rc.now,
            is_exploring=rc.is_exploring,
            clusters=self.latest_clusters,
            min_frontier_size=rc.params.min_frontier_size,
            map_info=rc.map_info,
            blacklist=rc.blacklist,
            goal_xy=rc.goal_xy,
        )

    def exhaustion_report(self, rc: RenderContext) -> str:
        return format_frontier_exhaustion(
            self.latest_clusters, rc.map_info, rc.robot_xy,
            rc.params, rc.blacklist, NO_FRONTIER_PATIENCE,
        )

    def failure_report(self, rc: RenderContext) -> str:
        return format_cluster_summary(self.latest_clusters, rc.map_info)

    def telemetry_extra(self) -> dict:
        # Extra no_frontier telemetry fields the node merges in blindly.
        diag = self.latest_diag or {}
        return {"raw_clusters": len(self.latest_clusters), **diag}
