"""Extractors for Pod and workload controller kinds."""

from __future__ import annotations

from graphnetes.models import Confidence, EdgeRelation, ResourceEdge, ResourceKind, ResourceNode
from graphnetes.extract.registry import ExtractorRegistry
from graphnetes.extract.helpers import Raw, Extracted, manifest_result, namespace_edge, owner_edges
from graphnetes.extract.models import DaemonSet, Deployment, Pod, ReplicaSet, StatefulSet


def _workload_node(kind: ResourceKind, model) -> ResourceNode:
    return ResourceNode.from_resource(
        kind=kind,
        name=model.name,
        namespace=model.namespace,
        labels=model.labels,
        annotations=model.annotations,
        metadata={"replicas": getattr(model, "replicas", None), "selector": model.selector},
    )


def _extract_workload(kind: ResourceKind, cls, raw: Raw) -> Extracted:
    model = cls.from_dict(raw)
    node = _workload_node(kind, model)
    edges: list[ResourceEdge] = []
    edges.extend(owner_edges(kind, model.name, model.namespace, model.owner_references))
    edges.append(namespace_edge(kind, model.name, model.namespace))
    nodes = [node]
    if pair := manifest_result(raw, node.id):
        nodes.append(pair[0])
        edges.append(pair[1])
    return nodes, edges


_SIMPLE_WORKLOADS = (
    ("Deployment", ResourceKind.DEPLOYMENT, Deployment),
    ("ReplicaSet", ResourceKind.REPLICA_SET, ReplicaSet),
    ("DaemonSet", ResourceKind.DAEMON_SET, DaemonSet),
)

for _name, _kind, _cls in _SIMPLE_WORKLOADS:
    ExtractorRegistry.register(_name)(lambda raw, k=_kind, c=_cls: _extract_workload(k, c, raw))


@ExtractorRegistry.register("StatefulSet")
def extract_stateful_set(raw: Raw) -> Extracted:
    nodes, edges = _extract_workload(ResourceKind.STATEFUL_SET, StatefulSet, raw)
    model = StatefulSet.from_dict(raw)
    for name in model.volume_claim_template_names:
        # The k8s API can return volume claim templates with a null metadata block,
        # producing an empty string here.
        if name:
            edges.append(ResourceEdge(
                source_id=nodes[0].id,
                target_id=ResourceNode.make_id(ResourceKind.PERSISTENT_VOLUME_CLAIM, name, model.namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))
    return nodes, edges


def _volume_edges(node_id: str, namespace: str, volumes) -> list[ResourceEdge]:
    edges = []
    for volume in volumes:
        if volume.config_map:
            edges.append(ResourceEdge(
                source_id=node_id,
                target_id=ResourceNode.make_id(ResourceKind.CONFIG_MAP, volume.config_map, namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))
        if volume.secret:
            edges.append(ResourceEdge(
                source_id=node_id,
                target_id=ResourceNode.make_id(ResourceKind.SECRET, volume.secret, namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))
        if volume.persistent_volume_claim:
            edges.append(ResourceEdge(
                source_id=node_id,
                target_id=ResourceNode.make_id(ResourceKind.PERSISTENT_VOLUME_CLAIM, volume.persistent_volume_claim, namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))
    return edges


@ExtractorRegistry.register("Pod")
def extract_pod(raw: Raw) -> Extracted:
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
    edges.extend(_volume_edges(node.id, pod.namespace, pod.volumes))
    nodes = [node]
    if pair := manifest_result(raw, node.id):
        nodes.append(pair[0])
        edges.append(pair[1])
    return nodes, edges
