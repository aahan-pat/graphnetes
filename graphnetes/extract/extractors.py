"""Per-kind extractor functions and the EXTRACTORS registry.

Each function takes a raw k8s API dict and returns all nodes and edges
derived from that resource.
"""

from __future__ import annotations

from typing import Any, Callable

from graphnetes.models import Confidence, EdgeRelation, ResourceEdge, ResourceKind, ResourceNode

from .helpers import manifest_result, namespace_edge, owner_edges
from .models import DaemonSet, Deployment, Pod, ReplicaSet, StatefulSet

RawResource = dict[str, Any]
Extracted = tuple[list[ResourceNode], list[ResourceEdge]]


def extract_pod(raw: RawResource) -> Extracted:
    pod = Pod.from_dict(raw)
    node = ResourceNode.from_resource(
        kind=ResourceKind.POD,
        name=pod.name,
        namespace=pod.namespace,
        labels=pod.labels,
        annotations=pod.annotations,
    )
    edges: list[ResourceEdge] = []
    edges.extend(owner_edges(ResourceKind.POD, pod.name, pod.namespace, pod.owner_references))
    edges.append(namespace_edge(ResourceKind.POD, pod.name, pod.namespace))

    if pod.node_name:
        edges.append(ResourceEdge(
            source_id=node.id,
            target_id=ResourceNode.make_id(ResourceKind.NODE, pod.node_name, None),
            relation=EdgeRelation.SCHEDULED_ON,
            confidence=Confidence.EXTRACTED,
        ))
    if pod.service_account_name:
        edges.append(ResourceEdge(
            source_id=node.id,
            target_id=ResourceNode.make_id(ResourceKind.SERVICE_ACCOUNT, pod.service_account_name, pod.namespace),
            relation=EdgeRelation.USES_SERVICE_ACCOUNT,
            confidence=Confidence.EXTRACTED,
        ))
    for vol in pod.volumes:
        if vol.config_map:
            edges.append(ResourceEdge(
                source_id=node.id,
                target_id=ResourceNode.make_id(ResourceKind.CONFIG_MAP, vol.config_map, pod.namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))
        if vol.secret:
            edges.append(ResourceEdge(
                source_id=node.id,
                target_id=ResourceNode.make_id(ResourceKind.SECRET, vol.secret, pod.namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))
        if vol.persistent_volume_claim:
            edges.append(ResourceEdge(
                source_id=node.id,
                target_id=ResourceNode.make_id(ResourceKind.PERSISTENT_VOLUME_CLAIM, vol.persistent_volume_claim, pod.namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))

    nodes = [node]
    if pair := manifest_result(raw, node.id):
        nodes.append(pair[0])
        edges.append(pair[1])
    return nodes, edges


def _workload_node(kind: ResourceKind, model: Any) -> ResourceNode:
    return ResourceNode.from_resource(
        kind=kind,
        name=model.name,
        namespace=model.namespace,
        labels=model.labels,
        annotations=model.annotations,
        metadata={"replicas": getattr(model, "replicas", None), "selector": model.selector},
    )


def _extract_workload(kind: ResourceKind, model_cls: Any, raw: RawResource) -> Extracted:
    model = model_cls.from_dict(raw)
    node = _workload_node(kind, model)
    edges: list[ResourceEdge] = []
    edges.extend(owner_edges(kind, model.name, model.namespace, model.owner_references))
    edges.append(namespace_edge(kind, model.name, model.namespace))
    nodes = [node]
    if pair := manifest_result(raw, node.id):
        nodes.append(pair[0])
        edges.append(pair[1])
    return nodes, edges


def extract_deployment(raw: RawResource) -> Extracted:
    return _extract_workload(ResourceKind.DEPLOYMENT, Deployment, raw)


def extract_replica_set(raw: RawResource) -> Extracted:
    return _extract_workload(ResourceKind.REPLICA_SET, ReplicaSet, raw)


def extract_daemon_set(raw: RawResource) -> Extracted:
    return _extract_workload(ResourceKind.DAEMON_SET, DaemonSet, raw)


def extract_stateful_set(raw: RawResource) -> Extracted:
    model = StatefulSet.from_dict(raw)
    node = _workload_node(ResourceKind.STATEFUL_SET, model)
    edges: list[ResourceEdge] = []
    edges.extend(owner_edges(ResourceKind.STATEFUL_SET, model.name, model.namespace, model.owner_references))
    edges.append(namespace_edge(ResourceKind.STATEFUL_SET, model.name, model.namespace))
    for name in model.volume_claim_template_names:
        if name:
            edges.append(ResourceEdge(
                source_id=node.id,
                target_id=ResourceNode.make_id(ResourceKind.PERSISTENT_VOLUME_CLAIM, name, model.namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))
    nodes = [node]
    if pair := manifest_result(raw, node.id):
        nodes.append(pair[0])
        edges.append(pair[1])
    return nodes, edges


EXTRACTORS: dict[str, Callable[[RawResource], Extracted]] = {
    "Pod": extract_pod,
    "Deployment": extract_deployment,
    "ReplicaSet": extract_replica_set,
    "StatefulSet": extract_stateful_set,
    "DaemonSet": extract_daemon_set,
}
