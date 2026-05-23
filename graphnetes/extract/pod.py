"""
Extractor for Pod resources.

Produces one ResourceNode per pod and edges for every relationship
the pod participates in: ownership, scheduling, service account,
volume mounts, and namespace membership.
"""

from graphnetes.models import (
    Confidence,
    EdgeRelation,
    ResourceEdge,
    ResourceKind,
    ResourceNode,
)
from graphnetes.models.pod import Pod

from .base import BaseExtractor, RawResource


class PodExtractor(BaseExtractor):
    def extract_node(self, resource: RawResource) -> ResourceNode:
        """Return the ResourceNode for the pod."""
        pod = Pod.from_dict(resource)

        return ResourceNode.from_resource(
            kind=ResourceKind.POD,
            name=pod.name,
            namespace=pod.namespace,
            labels=pod.labels,
        )

    def extract_edges(self, resource: RawResource) -> list[ResourceEdge]:
        """
        Return edges for all relationships the pod participates in.

        Edges produced:
          - owns:                 OwnerReference (ReplicaSet/Job) → Pod
          - scheduled_on:         Pod → Node
          - uses_service_account: Pod → ServiceAccount
          - mounts:               Pod → ConfigMap / Secret / PVC
          - in_namespace:         Pod → Namespace
        """
        pod = Pod.from_dict(resource)
        edges: list[ResourceEdge] = []

        edges.extend(self._extract_owner_edges(pod))

        if edge := self._extract_scheduled_on_edge(pod):
            edges.append(edge)

        if edge := self._extract_service_account_edge(pod):
            edges.append(edge)

        edges.extend(self._extract_mount_edges(pod))
        edges.append(self._extract_namespace_edge(pod))

        return edges

    def _extract_owner_edges(self, pod: Pod) -> list[ResourceEdge]:
        """Build owns edges from owner_references."""
        pod_id = ResourceNode.make_id(ResourceKind.POD, pod.name, pod.namespace)
        edges = []

        for ref in pod.owner_references:
            owner_id = ResourceNode.make_id(
                ResourceKind.from_str(ref.kind),
                ref.name,
                pod.namespace,
            )
            edges.append(ResourceEdge(
                source_id=owner_id,
                target_id=pod_id,
                relation=EdgeRelation.OWNS,
                confidence=Confidence.EXTRACTED,
            ))

        return edges

    def _extract_scheduled_on_edge(self, pod: Pod) -> ResourceEdge | None:
        """Build scheduled_on edge from spec.node_name."""
        if not pod.node_name:
            return None

        return ResourceEdge(
            source_id=ResourceNode.make_id(ResourceKind.POD, pod.name, pod.namespace),
            target_id=ResourceNode.make_id(ResourceKind.NODE, pod.node_name, None),
            relation=EdgeRelation.SCHEDULED_ON,
            confidence=Confidence.EXTRACTED,
        )

    def _extract_service_account_edge(self, pod: Pod) -> ResourceEdge | None:
        """Build uses_service_account edge from spec.service_account_name."""
        if not pod.service_account_name:
            return None

        return ResourceEdge(
            source_id=ResourceNode.make_id(ResourceKind.POD, pod.name, pod.namespace),
            target_id=ResourceNode.make_id(ResourceKind.SERVICE_ACCOUNT, pod.service_account_name, pod.namespace),
            relation=EdgeRelation.USES_SERVICE_ACCOUNT,
            confidence=Confidence.EXTRACTED,
        )

    def _extract_mount_edges(self, pod: Pod) -> list[ResourceEdge]:
        """Build mounts edges from spec.volumes for ConfigMap, Secret, and PVC volumes."""
        pod_id = ResourceNode.make_id(ResourceKind.POD, pod.name, pod.namespace)
        edges = []

        for vol in pod.volumes:
            if vol.config_map:
                edges.append(ResourceEdge(
                    source_id=pod_id,
                    target_id=ResourceNode.make_id(ResourceKind.CONFIG_MAP, vol.config_map, pod.namespace),
                    relation=EdgeRelation.MOUNTS,
                    confidence=Confidence.EXTRACTED,
                ))
            if vol.secret:
                edges.append(ResourceEdge(
                    source_id=pod_id,
                    target_id=ResourceNode.make_id(ResourceKind.SECRET, vol.secret, pod.namespace),
                    relation=EdgeRelation.MOUNTS,
                    confidence=Confidence.EXTRACTED,
                ))
            if vol.persistent_volume_claim:
                edges.append(ResourceEdge(
                    source_id=pod_id,
                    target_id=ResourceNode.make_id(ResourceKind.PERSISTENT_VOLUME_CLAIM, vol.persistent_volume_claim, pod.namespace),
                    relation=EdgeRelation.MOUNTS,
                    confidence=Confidence.EXTRACTED,
                ))

        return edges

    def _extract_namespace_edge(self, pod: Pod) -> ResourceEdge:
        """Build in_namespace edge from metadata.namespace."""
        return ResourceEdge(
            source_id=ResourceNode.make_id(ResourceKind.POD, pod.name, pod.namespace),
            target_id=ResourceNode.make_id(ResourceKind.NAMESPACE, pod.namespace, None),
            relation=EdgeRelation.IN_NAMESPACE,
            confidence=Confidence.EXTRACTED,
        )
