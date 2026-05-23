"""
Constructs and maintains the NetworkX DiGraph from extracted nodes and edges.

Provides O(1) lookup indexes by (kind, namespace, name) and by namespace
for subgraph queries.
"""

from __future__ import annotations

from collections import Counter

import networkx as nx

from graphnetes.models import ResourceEdge, ResourceKind, ResourceNode


class GraphBuilder:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()

        # (kind, namespace, name) → node_id
        self._kind_index: dict[tuple[ResourceKind, str | None, str], str] = {}

        # namespace → list of node_ids
        self._namespace_index: dict[str, list[str]] = {}

    def add_node(self, node: ResourceNode) -> None:
        """Add a ResourceNode to the graph and update indexes."""
        self.graph.add_node(node.id, data=node)
        self._kind_index[(node.kind, node.namespace, node.name)] = node.id
        if node.namespace:
            self._namespace_index.setdefault(node.namespace, []).append(node.id)

    def add_edge(self, edge: ResourceEdge) -> None:
        """Add a ResourceEdge to the graph."""
        self.graph.add_edge(edge.source_id, edge.target_id, data=edge)

    def add_nodes(self, nodes: list[ResourceNode]) -> None:
        """Add multiple nodes."""
        for node in nodes:
            self.add_node(node)

    def add_edges(self, edges: list[ResourceEdge]) -> None:
        """Add multiple edges."""
        for edge in edges:
            self.add_edge(edge)

    def get_node(self, kind: ResourceKind, name: str, namespace: str | None = None) -> ResourceNode | None:
        """Look up a node by kind, name, and namespace. Returns None if not found."""
        node_id = self._kind_index.get((kind, namespace, name))
        if node_id is None:
            return None
        return self.graph.nodes[node_id]["data"]

    def get_namespace_subgraph(self, namespace: str) -> nx.DiGraph:
        """Return a subgraph scoped to a single namespace."""
        node_ids = self._namespace_index.get(namespace, [])
        return self.graph.subgraph(node_ids)

    def stats(self) -> dict:
        """Return node count, edge count, and breakdown by kind."""
        kind_counts = Counter(
            self.graph.nodes[n]["data"].kind.value
            for n in self.graph.nodes
            if "data" in self.graph.nodes[n]
        )
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "by_kind": dict(kind_counts),
        }
