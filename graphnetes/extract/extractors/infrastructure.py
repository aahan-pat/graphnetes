"""Extractors for infrastructure kinds: Namespace, Node, HorizontalPodAutoscaler."""

from __future__ import annotations

from graphnetes.models import Confidence, EdgeRelation, ResourceEdge, ResourceKind, ResourceNode
from graphnetes.extract import ExtractorRegistry
from graphnetes.extract.helpers import Extracted, Raw, namespace_edge, parse_metadata

_SCALE_TARGET_KINDS: dict[str, ResourceKind] = {
    "Deployment": ResourceKind.DEPLOYMENT,
    "StatefulSet": ResourceKind.STATEFUL_SET,
}


@ExtractorRegistry.register("Namespace")
def extract_namespace(raw: Raw) -> Extracted:
    name, _, labels, annotations = parse_metadata(raw)
    status = raw.get("status") or {}

    node = ResourceNode.from_resource(
        kind=ResourceKind.NAMESPACE,
        name=name,
        namespace=None,
        labels=labels,
        annotations=annotations,
        metadata={"phase": status.get("phase")},
    )
    return [node], []


@ExtractorRegistry.register("Node")
def extract_node(raw: Raw) -> Extracted:
    name, _, labels, annotations = parse_metadata(raw)
    status = raw.get("status") or {}

    # Flatten conditions list into a {type: status} dict for easy sidebar display.
    conditions = {
        c["type"]: c["status"]
        for c in (status.get("conditions") or [])
        if c.get("type")
    }

    node = ResourceNode.from_resource(
        kind=ResourceKind.NODE,
        name=name,
        namespace=None,
        labels=labels,
        annotations=annotations,
        metadata={
            "conditions": conditions,
            "allocatable": status.get("allocatable") or {},
        },
    )
    return [node], []


@ExtractorRegistry.register("HorizontalPodAutoscaler")
def extract_hpa(raw: Raw) -> Extracted:
    name, namespace, labels, annotations = parse_metadata(raw)
    spec = raw.get("spec") or {}
    target_ref = spec.get("scale_target_ref") or {}

    target_kind_str = target_ref.get("kind")
    target_name = target_ref.get("name")

    node = ResourceNode.from_resource(
        kind=ResourceKind.HORIZONTAL_POD_AUTOSCALER,
        name=name,
        namespace=namespace,
        labels=labels,
        annotations=annotations,
        metadata={
            "min_replicas": spec.get("min_replicas"),
            "max_replicas": spec.get("max_replicas"),
            "target_kind": target_kind_str,
            "target_name": target_name,
        },
    )

    edges: list[ResourceEdge] = [namespace_edge(ResourceKind.HORIZONTAL_POD_AUTOSCALER, name, namespace)]

    target_kind = _SCALE_TARGET_KINDS.get(target_kind_str or "")
    if target_kind and target_name:
        edges.append(ResourceEdge(
            source_id=node.id,
            target_id=ResourceNode.make_id(target_kind, target_name, namespace),
            relation=EdgeRelation.SCALES,
            confidence=Confidence.EXTRACTED,
        ))

    return [node], edges
