"""
Abstract base class for all resource extractors.

Each extractor takes a typed resource model and produces the nodes and edges
that represent it in the graph.
"""

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
