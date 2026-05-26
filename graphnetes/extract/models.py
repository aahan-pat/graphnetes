"""Internal parsing types for the extract layer.

These dataclasses are intermediate representations — they parse raw k8s API
dicts into typed objects that the extractor functions then convert into
ResourceNode and ResourceEdge instances. They are not shared outside extract/.

When to add a model here vs parsing inline in the extractor:

  Add a model when the resource has nested structures (e.g. volumes, containers,
  owner references) or enough fields that from_dict would exceed ~6 lines. The
  model isolates k8s parsing quirks (None-returning fields, nested dicts) from
  edge-building logic and makes the extractor readable.

  Parse inline when the resource only has flat fields readable in a few lines of
  standard `or {}` chains. ConfigMap, Secret, Namespace, ServiceAccount, and
  Service are examples where a model class would add ceremony without clarity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OwnerReference:
    kind: str
    name: str
    uid: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> OwnerReference:
        return cls(kind=raw["kind"], name=raw["name"], uid=raw["uid"])


@dataclass
class VolumeMount:
    name: str
    mount_path: str
    read_only: bool

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> VolumeMount:
        return cls(
            name=raw["name"],
            mount_path=raw["mount_path"],
            read_only=raw.get("read_only") or False,
        )


@dataclass
class Container:
    name: str
    image: str
    volume_mounts: list[VolumeMount] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Container:
        return cls(
            name=raw["name"],
            image=raw["image"],
            volume_mounts=[VolumeMount.from_dict(mount) for mount in raw.get("volume_mounts") or []],
        )


@dataclass
class Volume:
    name: str
    # At most one of these is set per volume.
    config_map: str | None = None
    secret: str | None = None
    persistent_volume_claim: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Volume:
        # The k8s Python client returns None for absent optional nested objects, not a
        # missing key, so `or {}` is required before chaining .get().
        config_map = (raw.get("config_map") or {}).get("name")
        secret = (raw.get("secret") or {}).get("secret_name")
        persistent_volume_claim = (raw.get("persistent_volume_claim") or {}).get("claim_name")
        return cls(
            name=raw["name"],
            config_map=config_map,
            secret=secret,
            persistent_volume_claim=persistent_volume_claim,
        )


@dataclass
class PodCondition:
    type: str
    status: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> PodCondition:
        return cls(type=raw["type"], status=raw["status"])


@dataclass
class Pod:
    name: str
    namespace: str
    uid: str
    labels: dict[str, str]
    annotations: dict[str, str]
    owner_references: list[OwnerReference]
    node_name: str | None
    service_account_name: str | None
    containers: list[Container]
    volumes: list[Volume]
    phase: str | None
    conditions: list[PodCondition]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Pod:
        metadata = raw.get("metadata") or {}
        spec = raw.get("spec") or {}
        status = raw.get("status") or {}
        return cls(
            name=metadata["name"],
            namespace=metadata["namespace"],
            uid=metadata["uid"],
            labels=metadata.get("labels") or {},
            annotations=metadata.get("annotations") or {},
            owner_references=[OwnerReference.from_dict(owner) for owner in metadata.get("owner_references") or []],
            node_name=spec.get("node_name"),
            service_account_name=spec.get("service_account_name"),
            containers=[Container.from_dict(container) for container in spec.get("containers") or []],
            volumes=[Volume.from_dict(volume) for volume in spec.get("volumes") or []],
            phase=status.get("phase"),
            conditions=[PodCondition.from_dict(condition) for condition in status.get("conditions") or []],
        )


@dataclass
class Deployment:
    name: str
    namespace: str
    uid: str
    labels: dict[str, str]
    annotations: dict[str, str]
    owner_references: list[OwnerReference]
    selector: dict[str, str]
    replicas: int | None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Deployment:
        metadata = raw.get("metadata") or {}
        spec = raw.get("spec") or {}
        return cls(
            name=metadata["name"],
            namespace=metadata["namespace"],
            uid=metadata["uid"],
            labels=metadata.get("labels") or {},
            annotations=metadata.get("annotations") or {},
            owner_references=[OwnerReference.from_dict(owner) for owner in metadata.get("owner_references") or []],
            selector=(spec.get("selector") or {}).get("match_labels") or {},
            replicas=spec.get("replicas"),
        )


@dataclass
class ReplicaSet:
    name: str
    namespace: str
    uid: str
    labels: dict[str, str]
    annotations: dict[str, str]
    owner_references: list[OwnerReference]
    selector: dict[str, str]
    replicas: int | None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ReplicaSet:
        metadata = raw.get("metadata") or {}
        spec = raw.get("spec") or {}
        return cls(
            name=metadata["name"],
            namespace=metadata["namespace"],
            uid=metadata["uid"],
            labels=metadata.get("labels") or {},
            annotations=metadata.get("annotations") or {},
            owner_references=[OwnerReference.from_dict(owner) for owner in metadata.get("owner_references") or []],
            selector=(spec.get("selector") or {}).get("match_labels") or {},
            replicas=spec.get("replicas"),
        )


@dataclass
class StatefulSet:
    name: str
    namespace: str
    uid: str
    labels: dict[str, str]
    annotations: dict[str, str]
    owner_references: list[OwnerReference]
    selector: dict[str, str]
    replicas: int | None
    volume_claim_template_names: list[str]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> StatefulSet:
        metadata = raw.get("metadata") or {}
        spec = raw.get("spec") or {}
        return cls(
            name=metadata["name"],
            namespace=metadata["namespace"],
            uid=metadata["uid"],
            labels=metadata.get("labels") or {},
            annotations=metadata.get("annotations") or {},
            owner_references=[OwnerReference.from_dict(owner) for owner in metadata.get("owner_references") or []],
            selector=(spec.get("selector") or {}).get("match_labels") or {},
            replicas=spec.get("replicas"),
            volume_claim_template_names=[
                (template.get("metadata") or {}).get("name", "")
                for template in spec.get("volume_claim_templates") or []
            ],
        )


@dataclass
class DaemonSet:
    name: str
    namespace: str
    uid: str
    labels: dict[str, str]
    annotations: dict[str, str]
    owner_references: list[OwnerReference]
    selector: dict[str, str]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> DaemonSet:
        metadata = raw.get("metadata") or {}
        spec = raw.get("spec") or {}
        return cls(
            name=metadata["name"],
            namespace=metadata["namespace"],
            uid=metadata["uid"],
            labels=metadata.get("labels") or {},
            annotations=metadata.get("annotations") or {},
            owner_references=[OwnerReference.from_dict(owner) for owner in metadata.get("owner_references") or []],
            selector=(spec.get("selector") or {}).get("match_labels") or {},
        )
