"""
Live ingestion — connects to a cluster and streams real-time resource change events.

Uses the kubernetes watch API to listen for ADDED, MODIFIED, and DELETED events
across all supported resource kinds. Intended to keep an already-built graph
up to date without a full rebuild.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncGenerator


# A Kubernetes resource as returned by the SDK's .to_dict() — untyped, unvalidated.
RawResource = dict[str, Any]


class EventType(str, Enum):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"


@dataclass
class WatchEvent:
    type: EventType
    resource: RawResource


async def watch_namespace(
    namespace: str,
    context: str | None = None,
) -> AsyncGenerator[WatchEvent, None]:
    """Stream watch events for all resources in a single namespace."""
    raise NotImplementedError


async def watch_cluster(
    context: str | None = None,
) -> AsyncGenerator[WatchEvent, None]:
    """Stream watch events for all resources across every namespace in the cluster."""
    raise NotImplementedError


async def watch(
    context: str | None = None,
    namespace: str | None = None,
    kubeconfig: str | None = None,
) -> AsyncGenerator[WatchEvent, None]:
    """
    Main entry point for live ingestion.

    If namespace is given, scopes the watch to that namespace only.
    Otherwise watches the full cluster.
    """
    raise NotImplementedError
