"""
Constructs and maintains the NetworkX DiGraph from extracted nodes and edges.

Provides O(1) lookup indexes by (kind, namespace, name) and by namespace
for subgraph queries.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

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

    def get_node_by_id(self, node_id: str) -> ResourceNode | None:
        """Look up a node by its full ID string. Returns None if not found or a stub."""
        node_data = self.graph.nodes.get(node_id)
        if node_data is None or "data" not in node_data:
            return None
        return node_data["data"]

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
        """Build selects edges between selectors and Pods by matching label selectors.

        Runs as a post-processing pass after all nodes are added. For each node that
        carries a selector in its metadata, checks every Pod node to see whether the
        selector labels are a subset of the Pod's labels. Adds a selects edge for each
        match.

        Kinds covered: Deployment, ReplicaSet, StatefulSet, DaemonSet, Service.
        """
        controller_kinds = [
            ResourceKind.DEPLOYMENT,
            ResourceKind.REPLICA_SET,
            ResourceKind.STATEFUL_SET,
            ResourceKind.DAEMON_SET,
            ResourceKind.SERVICE,
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

    def shortest_path(self, source_id: str, target_id: str) -> list[ResourceNode]:
        """Return the ResourceNode objects on the shortest directed path between two nodes."""
        try:
            ids = nx.shortest_path(self.graph, source=source_id, target=target_id)
        except nx.NetworkXNoPath:
            raise ValueError(f"no path from {source_id!r} to {target_id!r}")
        except nx.NodeNotFound as e:
            raise ValueError(str(e))
        return [self.graph.nodes[node_id]["data"] for node_id in ids]

    @classmethod
    def load(cls, path: Path) -> GraphBuilder:
        """Reconstruct a GraphBuilder from a graph.json produced by export_json."""
        data = json.loads(path.read_text())
        builder = cls()
        for node_dict in data["nodes"]:
            node = ResourceNode.from_resource(
                kind=ResourceKind.from_str(node_dict["kind"]),
                name=node_dict["name"],
                namespace=node_dict.get("namespace"),
                labels=node_dict.get("labels") or {},
                metadata=node_dict.get("metadata") or {},
            )
            builder.add_node(node)
        for edge_dict in data["edges"]:
            edge = ResourceEdge(
                source_id=edge_dict["source"],
                target_id=edge_dict["target"],
                relation=EdgeRelation(edge_dict["relation"]),
                confidence=Confidence(edge_dict["confidence"]),
                weight=edge_dict.get("weight", 1.0),
            )
            builder.add_edge(edge)
        return builder

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
