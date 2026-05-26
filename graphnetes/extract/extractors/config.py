"""Extractors for config and identity kinds: ConfigMap, Secret, ServiceAccount."""

from __future__ import annotations

from graphnetes.models import ResourceKind, ResourceNode
from graphnetes.extract import ExtractorRegistry
from graphnetes.extract.helpers import Extracted, Raw, namespace_edge, parse_metadata


@ExtractorRegistry.register("ConfigMap")
def extract_config_map(raw: Raw) -> Extracted:
    name, namespace, labels, annotations = parse_metadata(raw)
    # Store key names only — values may contain sensitive data.
    keys = list((raw.get("data") or {}).keys())

    node = ResourceNode.from_resource(
        kind=ResourceKind.CONFIG_MAP,
        name=name,
        namespace=namespace,
        labels=labels,
        annotations=annotations,
        metadata={"keys": keys},
    )
    return [node], [namespace_edge(ResourceKind.CONFIG_MAP, name, namespace)]


@ExtractorRegistry.register("ServiceAccount")
def extract_service_account(raw: Raw) -> Extracted:
    name, namespace, labels, annotations = parse_metadata(raw)

    node = ResourceNode.from_resource(
        kind=ResourceKind.SERVICE_ACCOUNT,
        name=name,
        namespace=namespace,
        labels=labels,
        annotations=annotations,
    )
    return [node], [namespace_edge(ResourceKind.SERVICE_ACCOUNT, name, namespace)]

@ExtractorRegistry.register("Secret")
def extract_secret(raw: Raw) -> Extracted:
    name, namespace, labels, annotations = parse_metadata(raw)

    node = ResourceNode.from_resource(
        kind=ResourceKind.SECRET,
        name=name,
        namespace=namespace,
        labels=labels,
        annotations=annotations,
    )
    return [node], [namespace_edge(ResourceKind.SECRET, name, namespace)]