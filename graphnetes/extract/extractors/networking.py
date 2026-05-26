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

    # Collect all service names referenced across rules and the default backend.
    service_names: list[str] = []
    for rule in (spec.get("rules") or []):
        http = (rule or {}).get("http") or {}
        for path in (http.get("paths") or []):
            svc = ((path or {}).get("backend") or {}).get("service") or {}
            if svc_name := svc.get("name"):
                service_names.append(svc_name)

    default_svc = (spec.get("default_backend") or {}).get("service") or {}
    if svc_name := default_svc.get("name"):
        service_names.append(svc_name)

    for svc_name in service_names:
        edges.append(ResourceEdge(
            source_id=node.id,
            target_id=ResourceNode.make_id(ResourceKind.SERVICE, svc_name, namespace),
            relation=EdgeRelation.ROUTES_TO,
            confidence=Confidence.EXTRACTED,
        ))

    return [node], edges
