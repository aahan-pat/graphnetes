"""
Exports the built graph to persistent output formats.

Writes graph.json (node-link JSON) and graph.html (self-contained
browser visualization) to the output directory.
"""

import json
from pathlib import Path
from typing import Any

from graphnetes.build.graph import GraphBuilder

from _template import HTML_TEMPLATE


def _stub_node_from_id(node_id: str) -> dict[str, Any]:
    """
    Build a minimal node dict for nodes that appear as edge targets but were never ingested.

    NetworkX auto-creates an attribute-less node whenever add_edge references an unknown ID.
    This happens for resource kinds we don't fetch yet (Namespace, Node, ServiceAccount, etc.).
    Without this, the visualizer silently drops every edge pointing to one of those nodes.
    """
    parts = node_id.split("/")
    if len(parts) == 3:
        kind, namespace, name = parts
    elif len(parts) == 2:
        kind, name = parts
        namespace = None
    else:
        kind, name, namespace = "Unknown", node_id, None
    return {"id": node_id, "kind": kind, "name": name, "namespace": namespace, "labels": {}}


def _graph_to_dict(builder: GraphBuilder) -> dict[str, Any]:
    nodes = []
    for node_id in builder.graph.nodes:
        node_data = builder.graph.nodes[node_id]
        if "data" in node_data:
            nodes.append(node_data["data"].to_dict())
        else:
            nodes.append(_stub_node_from_id(node_id))

    edges = [
        builder.graph.edges[source, target]["data"].to_dict()
        for source, target in builder.graph.edges
    ]
    return {"nodes": nodes, "edges": edges}


def export_json(data: dict[str, Any], output: Path) -> Path:
    """Write graph.json to the output directory."""
    path = output / "graph.json"
    path.write_text(json.dumps(data, indent=2))
    return path


def export_html(data: dict[str, Any], output: Path) -> Path:
    """Write a self-contained graph.html to the output directory."""
    html = HTML_TEMPLATE.replace("__GRAPH_DATA__", json.dumps(data))
    path = output / "graph.html"
    path.write_text(html)
    return path


def export(builder: GraphBuilder, output: Path) -> None:
    """Export the graph to all formats in the output directory."""
    output.mkdir(parents=True, exist_ok=True)
    data = _graph_to_dict(builder)
    export_json(data, output)
    export_html(data, output)
