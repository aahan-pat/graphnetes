"""
Abstract base class for all resource extractors.

Each extractor takes a typed resource model and produces the nodes and edges
that represent it in the graph.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from graphnetes.models import ResourceEdge, ResourceNode


RawResource = dict[str, Any]


class BaseExtractor(ABC):
    @abstractmethod
    def extract_node(self, resource: RawResource) -> ResourceNode:
        """Return the node that represents this resource."""

    @abstractmethod
    def extract_edges(self, resource: RawResource) -> list[ResourceEdge]:
        """Return all edges that connect this resource to others."""

    def extract(self, resource: RawResource) -> tuple[ResourceNode, list[ResourceEdge]]:
        """Return node and edges together. Override to avoid parsing the resource twice."""
        return self.extract_node(resource), self.extract_edges(resource)
