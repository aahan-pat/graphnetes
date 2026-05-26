"""Shared CLI helpers: graph loading, node resolution, edge collection, and fuzzy suggestions."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from graphnetes.build.graph import GraphBuilder
from graphnetes.models import ResourceNode


def suggest_nodes(builder: GraphBuilder, query: str, limit: int = 5) -> list[str]:
    """Return up to limit node IDs that contain query as a case-insensitive substring."""
    lower = query.lower()
    return [
        node_id
        for node_id in builder.graph.nodes
        if lower in node_id.lower()
    ][:limit]


def load_graph(graph: Path, console: Console) -> GraphBuilder:
    """Load the graph from disk, or print an error and exit if the file does not exist."""
    if not graph.exists():
        console.print(f"[red]graph.json not found:[/red] {graph}. Run [bold]graphnetes build[/bold] first.")
        raise typer.Exit(code=1)
    return GraphBuilder.load(path=graph)


def resolve_node(builder: GraphBuilder, node_id: str, console: Console) -> ResourceNode:
    """Return the node for node_id, or print suggestions and exit if not found."""
    node = builder.get_node_by_id(node_id)
    if node is None:
        console.print(f"[red]Error:[/red] node '{node_id}' not found.")
        suggestions = suggest_nodes(builder, node_id)
        if suggestions:
            console.print("\nDid you mean:")
            for suggestion in suggestions:
                console.print(f"  {suggestion}")
        else:
            console.print("Run [bold]graphnetes viz[/bold] to browse available nodes.")
        raise typer.Exit(code=1)
    return node


def collect_edges(builder: GraphBuilder, node_id: str, direction: str = "both") -> tuple[list, list]:
    """Return (outgoing, incoming) edge dicts filtered by direction (in, out, or both)."""
    outgoing = [
        {"relation": builder.graph.edges[node_id, t]["data"].relation.value, "target": t}
        for t in builder.graph.successors(node_id)
    ] if direction in ("out", "both") else []
    incoming = [
        {"relation": builder.graph.edges[s, node_id]["data"].relation.value, "source": s}
        for s in builder.graph.predecessors(node_id)
    ] if direction in ("in", "both") else []
    return outgoing, incoming
