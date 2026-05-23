"""
Live ingestion — connects to a cluster and streams real-time resource change events.

Uses the kubernetes watch API to listen for ADDED, MODIFIED, and DELETED events
across all supported resource kinds. Intended to keep an already-built graph
up to date without a full rebuild.
"""

from typing import Any, AsyncGenerator, Optional
from enum import Enum


RawResource = dict[str, Any]


class EventType(str, Enum):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"


class WatchEvent:
    type: EventType
    resource: RawResource


async def watch_namespace(
    namespace: str,
    context: Optional[str] = None,
) -> AsyncGenerator[WatchEvent, None]:
    """Stream watch events for all resources in a single namespace."""
    raise NotImplementedError


async def watch_cluster(
    context: Optional[str] = None,
) -> AsyncGenerator[WatchEvent, None]:
    """Stream watch events for all resources across every namespace in the cluster."""
    raise NotImplementedError


async def watch(
    context: Optional[str] = None,
    namespace: Optional[str] = None,
    kubeconfig: Optional[str] = None,
) -> AsyncGenerator[WatchEvent, None]:
    """
    Main entry point for live ingestion.

    If namespace is given, scopes the watch to that namespace only.
    Otherwise watches the full cluster.
    """
    raise NotImplementedError
