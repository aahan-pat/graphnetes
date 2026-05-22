from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .resource_kind import ResourceKind


@dataclass
class ResourceNode:
    id: str                         # "{kind}/{namespace}/{name}" or "{kind}/{name}" for cluster-scoped
    kind: ResourceKind
    name: str
    namespace: str | None           # None for cluster-scoped resources
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def make_id(cls, kind: ResourceKind, name: str, namespace: str | None) -> str:
        if namespace:
            return f"{kind.value}/{namespace}/{name}"
        return f"{kind.value}/{name}"

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
