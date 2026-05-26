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


@ExtractorRegistry.register("Deployment")
def extract_deployment(raw: Raw) -> Extracted:
    return _extract_workload(ResourceKind.DEPLOYMENT, Deployment, raw)


@ExtractorRegistry.register("ReplicaSet")
def extract_replica_set(raw: Raw) -> Extracted:
    return _extract_workload(ResourceKind.REPLICA_SET, ReplicaSet, raw)


@ExtractorRegistry.register("DaemonSet")
def extract_daemon_set(raw: Raw) -> Extracted:
    return _extract_workload(ResourceKind.DAEMON_SET, DaemonSet, raw)


@ExtractorRegistry.register("StatefulSet")
def extract_stateful_set(raw: Raw) -> Extracted:
    model = StatefulSet.from_dict(raw)
    node = _workload_node(ResourceKind.STATEFUL_SET, model)
    edges: list[ResourceEdge] = []
    edges.extend(owner_edges(ResourceKind.STATEFUL_SET, model.name, model.namespace, model.owner_references))
    edges.append(namespace_edge(ResourceKind.STATEFUL_SET, model.name, model.namespace))
    for name in model.volume_claim_template_names:
        # The k8s API can return volume claim templates with a null metadata block,
        # producing an empty string here.
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
    for volume in pod.volumes:
        if volume.config_map:
            edges.append(ResourceEdge(
                source_id=node.id,
                target_id=ResourceNode.make_id(ResourceKind.CONFIG_MAP, volume.config_map, pod.namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))
        if volume.secret:
            edges.append(ResourceEdge(
                source_id=node.id,
                target_id=ResourceNode.make_id(ResourceKind.SECRET, volume.secret, pod.namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))
        if volume.persistent_volume_claim:
            edges.append(ResourceEdge(
                source_id=node.id,
                target_id=ResourceNode.make_id(ResourceKind.PERSISTENT_VOLUME_CLAIM, volume.persistent_volume_claim, pod.namespace),
                relation=EdgeRelation.MOUNTS,
                confidence=Confidence.EXTRACTED,
            ))

    nodes = [node]
    if pair := manifest_result(raw, node.id):
        nodes.append(pair[0])
        edges.append(pair[1])
    return nodes, edges
