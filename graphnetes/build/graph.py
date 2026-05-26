"""
Constructs and maintains the NetworkX DiGraph from extracted nodes and edges.

Provides O(1) lookup indexes by (kind, namespace, name) and by namespace
for subgraph queries.
"""

from __future__ import annotations

from collections import Counter

import networkx as nx

from graphnetes.models import Confidence, EdgeRelation, ResourceEdge, ResourceKind, ResourceNode


class GraphBuilder:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()

        # Keyed by (kind, namespace, name) for O(1) node lookup.
        self._kind_index: dict[tuple[ResourceKind, str | None, str], str] = {}

        # Keyed by namespace, each value is the list of node IDs in that namespace.
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

    def get_nodes_by_kind(self, kind: ResourceKind) -> list[ResourceNode]:
        """Return all nodes of a given kind."""
        # Nodes without a "data" attribute are stubs that NetworkX creates when an edge
        # references an ID that was never explicitly added.
        return [
            self.graph.nodes[node_id]["data"]
            for node_id in self.graph.nodes
            if "data" in self.graph.nodes[node_id] and self.graph.nodes[node_id]["data"].kind == kind
        ]

    def build_selector_edges(self) -> None:
        """Build selects edges between controllers and Pods by matching label selectors.

        Runs as a post-processing pass after all nodes are added. For each controller
        node that carries a selector in its metadata, checks every Pod node to see
        whether the selector labels are a subset of the Pod's labels. Adds a selects
        edge for each match.

        Controllers covered: Deployment, ReplicaSet, StatefulSet, DaemonSet.
        """
        controller_kinds = [
            ResourceKind.DEPLOYMENT,
            ResourceKind.REPLICA_SET,
            ResourceKind.STATEFUL_SET,
            ResourceKind.DAEMON_SET,
        ]
        pods = self.get_nodes_by_kind(ResourceKind.POD)

        for kind in controller_kinds:
            for controller in self.get_nodes_by_kind(kind):
                selector: dict[str, str] = controller.metadata.get("selector") or {}
                if not selector:
                    continue
                selector_items = selector.items()
                for pod in pods:
                    # dict_items supports <= as a subset test, returning True when every
                    # selector key-value pair is present in pod.labels.
                    if selector_items <= pod.labels.items():
                        self.add_edge(ResourceEdge(
                            source_id=controller.id,
                            target_id=pod.id,
                            relation=EdgeRelation.SELECTS,
                            confidence=Confidence.INFERRED,
                        ))

    def stats(self) -> dict:
        """Return node count, edge count, and breakdown by kind."""
        kind_counts = Counter(
            self.graph.nodes[node_id]["data"].kind.value
            for node_id in self.graph.nodes
            if "data" in self.graph.nodes[node_id]
        )
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "by_kind": dict(kind_counts),
        }
