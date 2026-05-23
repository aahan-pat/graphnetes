"""
Exports the built graph to persistent output formats.

Writes graph.json (node-link JSON) and graph.html (self-contained
browser visualization) to the output directory.
"""

import json
from pathlib import Path
from typing import Any

from graphnetes.build.graph import GraphBuilder

from ._template import HTML_TEMPLATE


def _stub_node_from_id(node_id: str) -> dict[str, Any]:
    """Build a minimal node dict for a stub node (referenced by an edge but not ingested)."""
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
    for n in builder.graph.nodes:
        node_data = builder.graph.nodes[n]
        if "data" in node_data:
            nodes.append(node_data["data"].to_dict())
        else:
            nodes.append(_stub_node_from_id(n))

    edges = [
        builder.graph.edges[u, v]["data"].to_dict()
        for u, v in builder.graph.edges
    ]
    return {"nodes": nodes, "edges": edges}


def export_json(builder: GraphBuilder, output: Path) -> Path:
    """Write graph.json to the output directory."""
    path = output / "graph.json"
    with open(path, "w") as f:
        json.dump(_graph_to_dict(builder), f, indent=2)
    return path


def export_html(builder: GraphBuilder, output: Path) -> Path:
    """Write a self-contained graph.html to the output directory."""
    graph_data = json.dumps(_graph_to_dict(builder))
    html = HTML_TEMPLATE.replace("__GRAPH_DATA__", graph_data)
    path = output / "graph.html"
    with open(path, "w") as f:
        f.write(html)
    return path


def export(builder: GraphBuilder, output: Path) -> None:
    """Export the graph to all formats in the output directory."""
    output.mkdir(parents=True, exist_ok=True)
    export_json(builder, output)
    export_html(builder, output)
