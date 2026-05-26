"""Extractors for networking kinds: Service, Ingress."""

from __future__ import annotations

from graphnetes.models import Confidence, EdgeRelation, ResourceEdge, ResourceKind, ResourceNode
from graphnetes.extract.registry import ExtractorRegistry
from graphnetes.extract.helpers import Extracted, Raw, namespace_edge, parse_metadata


@ExtractorRegistry.register("Service")
def extract_service(raw: Raw) -> Extracted:
    name, namespace, labels, annotations = parse_metadata(raw)
    spec = raw.get("spec") or {}

    node = ResourceNode.from_resource(
        kind=ResourceKind.SERVICE,
        name=name,
        namespace=namespace,
        labels=labels,
        annotations=annotations,
        metadata={
            "selector": spec.get("selector") or {},
            "type": spec.get("type"),
            "cluster_ip": spec.get("cluster_ip"),
        },
    )
    edges: list[ResourceEdge] = [namespace_edge(ResourceKind.SERVICE, name, namespace)]
    return [node], edges


def _service_names(spec: dict) -> list[str]:
    """Collect all service names referenced in Ingress rules and default backend."""
    names = []
    for rule in (spec.get("rules") or []):
        http = (rule or {}).get("http") or {}
        for path in (http.get("paths") or []):
            svc = ((path or {}).get("backend") or {}).get("service") or {}
            if name := svc.get("name"):
                names.append(name)
    default_svc = (spec.get("default_backend") or {}).get("service") or {}
    if name := default_svc.get("name"):
        names.append(name)
    return names


@ExtractorRegistry.register("Ingress")
def extract_ingress(raw: Raw) -> Extracted:
    name, namespace, labels, annotations = parse_metadata(raw)
    spec = raw.get("spec") or {}

    node = ResourceNode.from_resource(
        kind=ResourceKind.INGRESS,
        name=name,
        namespace=namespace,
        labels=labels,
        annotations=annotations,
    )

    edges: list[ResourceEdge] = [namespace_edge(ResourceKind.INGRESS, name, namespace)]
    for svc_name in _service_names(spec):
        edges.append(ResourceEdge(
            source_id=node.id,
            target_id=ResourceNode.make_id(ResourceKind.SERVICE, svc_name, namespace),
            relation=EdgeRelation.ROUTES_TO,
            confidence=Confidence.EXTRACTED,
        ))

    return [node], edges
