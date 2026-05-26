"""Shared CLI helpers: fuzzy node suggestions."""

from __future__ import annotations

from graphnetes.build.graph import GraphBuilder


def suggest_nodes(builder: GraphBuilder, query: str, limit: int = 5) -> list[str]:
    """Return up to limit node IDs that contain query as a case-insensitive substring."""
    lower = query.lower()
    return [
        node_id
        for node_id in builder.graph.nodes
        if lower in node_id.lower()
    ][:limit]
