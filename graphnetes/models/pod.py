from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OwnerReference:
    kind: str
    name: str
    uid: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> OwnerReference:
        return cls(
            kind=d["kind"],
            name=d["name"],
            uid=d["uid"],
        )


@dataclass
class VolumeMount:
    name: str
    mount_path: str
    read_only: bool

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VolumeMount:
        return cls(
            name=d["name"],
            mount_path=d["mount_path"],
            read_only=d.get("read_only") or False,
        )


@dataclass
class Container:
    name: str
    image: str
    volume_mounts: list[VolumeMount] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Container:
        return cls(
            name=d["name"],
            image=d["image"],
            volume_mounts=[VolumeMount.from_dict(v) for v in d.get("volume_mounts") or []],
        )


@dataclass
class Volume:
    name: str
    # At most one of these is set per volume
    config_map: str | None = None
    secret: str | None = None
    persistent_volume_claim: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Volume:
        config_map = None
        if cm := d.get("config_map"):
            config_map = cm.get("name")

        secret = None
        if s := d.get("secret"):
            secret = s.get("secret_name")

        pvc = None
        if p := d.get("persistent_volume_claim"):
            pvc = p.get("claim_name")

        return cls(
            name=d["name"],
            config_map=config_map,
            secret=secret,
            persistent_volume_claim=pvc,
        )


@dataclass
class PodCondition:
    type: str
    status: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PodCondition:
        return cls(
            type=d["type"],
            status=d["status"],
        )


@dataclass
class Pod:
    name: str
    namespace: str
    uid: str
    labels: dict[str, str]
    owner_references: list[OwnerReference]
    node_name: str | None
    service_account_name: str | None
    containers: list[Container]
    volumes: list[Volume]
    phase: str | None
    conditions: list[PodCondition]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Pod:
        metadata = d.get("metadata") or {}
        spec = d.get("spec") or {}
        status = d.get("status") or {}

        return cls(
            name=metadata["name"],
            namespace=metadata["namespace"],
            uid=metadata["uid"],
            labels=metadata.get("labels") or {},
            owner_references=[
                OwnerReference.from_dict(o)
                for o in metadata.get("owner_references") or []
            ],
            node_name=spec.get("node_name"),
            service_account_name=spec.get("service_account_name"),
            containers=[
                Container.from_dict(c)
                for c in spec.get("containers") or []
            ],
            volumes=[
                Volume.from_dict(v)
                for v in spec.get("volumes") or []
            ],
            phase=status.get("phase"),
            conditions=[
                PodCondition.from_dict(c)
                for c in status.get("conditions") or []
            ],
        )
