from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .resource_kind import ResourceKind


@dataclass
class ResourceNode:
    # "{kind}/{namespace}/{name}" or "{kind}/{name}" for cluster-scoped
    id: str
    kind: ResourceKind
    name: str
    # None for cluster-scoped resources
    namespace: str | None
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def make_id(cls, kind: ResourceKind, name: str, namespace: str | None) -> str:
        if namespace:
            return f"{kind.value}/{namespace}/{name}"
        return f"{kind.value}/{name}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "name": self.name,
            "namespace": self.namespace,
            "labels": self.labels,
            "metadata": self.metadata,
        }

    @classmethod
    def from_resource(
        cls,
        kind: ResourceKind,
        name: str,
        namespace: str | None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResourceNode:
        return cls(
            id=cls.make_id(kind, name, namespace),
            kind=kind,
            name=name,
            namespace=namespace,
            labels=labels or {},
            annotations=annotations or {},
            metadata=metadata or {},
        )
