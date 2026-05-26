"""Shared edge and node builders used across all extractor functions."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from graphnetes.models import Confidence, EdgeRelation, ResourceEdge, ResourceKind, ResourceNode

from .models import OwnerReference

_LAST_APPLIED = "kubectl.kubernetes.io/last-applied-configuration"


def owner_edges(
    kind: ResourceKind,
    name: str,
    namespace: str | None,
    refs: list[OwnerReference],
) -> list[ResourceEdge]:
    source_id = ResourceNode.make_id(kind, name, namespace)
    return [
        ResourceEdge(
            source_id=ResourceNode.make_id(ResourceKind.from_str(ref.kind), ref.name, namespace),
            target_id=source_id,
            relation=EdgeRelation.OWNS,
            confidence=Confidence.EXTRACTED,
        )
        for ref in refs
    ]


def namespace_edge(kind: ResourceKind, name: str, namespace: str) -> ResourceEdge:
    return ResourceEdge(
        source_id=ResourceNode.make_id(kind, name, namespace),
        target_id=ResourceNode.make_id(ResourceKind.NAMESPACE, namespace, None),
        relation=EdgeRelation.IN_NAMESPACE,
        confidence=Confidence.EXTRACTED,
    )


def manifest_result(raw: dict[str, Any], source_id: str) -> tuple[ResourceNode, ResourceEdge] | None:
    """Return a Manifest node and configured_by edge if the last-applied annotation is present."""
    annotations = (raw.get("metadata") or {}).get("annotations") or {}
    raw_annotation = annotations.get(_LAST_APPLIED)
    if not raw_annotation:
        return None
    digest = hashlib.sha256(raw_annotation.encode()).hexdigest()[:12]
    node = ResourceNode.from_resource(
        kind=ResourceKind.MANIFEST,
        name=digest,
        namespace=None,
        metadata={"spec": json.loads(raw_annotation)},
    )
    edge = ResourceEdge(
        source_id=source_id,
        target_id=node.id,
        relation=EdgeRelation.CONFIGURED_BY,
        confidence=Confidence.EXTRACTED,
    )
    return node, edge
