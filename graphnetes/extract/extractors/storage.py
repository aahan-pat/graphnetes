"""Extractors for storage kinds: PersistentVolume, PersistentVolumeClaim."""

from __future__ import annotations

from graphnetes.models import Confidence, EdgeRelation, ResourceEdge, ResourceKind, ResourceNode
from graphnetes.extract import ExtractorRegistry
from graphnetes.extract.helpers import Extracted, Raw, namespace_edge, parse_metadata


@ExtractorRegistry.register("PersistentVolume")
def extract_persistent_volume(raw: Raw) -> Extracted:
    name, _, labels, annotations = parse_metadata(raw)
    spec = raw.get("spec") or {}

    node = ResourceNode.from_resource(
        kind=ResourceKind.PERSISTENT_VOLUME,
        name=name,
        namespace=None,
        labels=labels,
        annotations=annotations,
        metadata={
            "capacity": spec.get("capacity") or {},
            "access_modes": spec.get("access_modes") or [],
            "storage_class": spec.get("storage_class_name"),
            "reclaim_policy": spec.get("persistent_volume_reclaim_policy"),
        },
    )
    return [node], []


@ExtractorRegistry.register("PersistentVolumeClaim")
def extract_persistent_volume_claim(raw: Raw) -> Extracted:
    name, namespace, labels, annotations = parse_metadata(raw)
    spec = raw.get("spec") or {}
    status = raw.get("status") or {}
    volume_name = spec.get("volume_name")

    node = ResourceNode.from_resource(
        kind=ResourceKind.PERSISTENT_VOLUME_CLAIM,
        name=name,
        namespace=namespace,
        labels=labels,
        annotations=annotations,
        metadata={
            "storage_class": spec.get("storage_class_name"),
            "phase": status.get("phase"),
        },
    )
    edges = [namespace_edge(ResourceKind.PERSISTENT_VOLUME_CLAIM, name, namespace)]
    if volume_name:
        edges.append(ResourceEdge(
            source_id=node.id,
            target_id=ResourceNode.make_id(ResourceKind.PERSISTENT_VOLUME, volume_name, None),
            relation=EdgeRelation.BOUND_TO,
            confidence=Confidence.EXTRACTED,
        ))
    return [node], edges
