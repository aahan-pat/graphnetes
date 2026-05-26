"""
Static ingestion — connects to a cluster and takes a one-time snapshot of all resources.

Fetches every supported resource kind across the cluster (or a single namespace)
and returns raw resource dicts. No watch; the graph reflects the cluster state
at the moment of the call.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Generator

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

# A Kubernetes resource as returned by the SDK's .to_dict() — untyped, unvalidated.
RawResource = dict[str, Any]

KUBECONFIG = Path.home() / ".kube" / "config"


def _is_excluded(kind: str, raw: RawResource, exclude: set[str]) -> bool:
    meta = raw.get("metadata") or {}
    if kind == "Namespace":
        return meta.get("name") in exclude
    return meta.get("namespace") in exclude


# Kubeconfig resolution
#
# Priority:
#   1. Explicit --kubeconfig flag
#   2. KUBECONFIG environment variable
#   3. ~/.kube/config
#   4. Error
class StaticIngestor:

    calls: list[tuple[str, str | None, str, str]] = []

    @staticmethod
    def register(client: str, namespaced: str | None, cluster: str, kind: str) -> None:
        """Register a Kubernetes API list call."""
        StaticIngestor.calls.append((client, namespaced, cluster, kind))

    def __init__(
        self,
        kubeconfig: str | None = None,
        context: str | None = None,
    ) -> None:
        kubeconfig_path = Path(kubeconfig) if kubeconfig else None

        configuration = client.Configuration()

        if kubeconfig_path:
            if not kubeconfig_path.exists():
                raise FileNotFoundError(f"kubeconfig not found: {kubeconfig_path}")
            config.load_kube_config(
                config_file=str(kubeconfig_path),
                context=context,
                client_configuration=configuration,
            )

        elif kubeconfig_env := os.environ.get("KUBECONFIG"):
            try:
                config.load_kube_config(
                    config_file=kubeconfig_env,
                    context=context,
                    client_configuration=configuration,
                )
            except ConfigException as e:
                raise RuntimeError(f"KUBECONFIG is set but could not be loaded: {e}") from e

        elif KUBECONFIG.exists():
            config.load_kube_config(
                config_file=str(KUBECONFIG),
                context=context,
                client_configuration=configuration,
            )

        else:
            raise RuntimeError(
                "No kubeconfig found. Provide --kubeconfig, set the KUBECONFIG "
                "environment variable, or ensure ~/.kube/config exists."
            )

        self.configuration = configuration
        self.api_client = client.ApiClient(configuration)
        self.v1 = client.CoreV1Api(self.api_client)
        self.apps_v1 = client.AppsV1Api(self.api_client)
        self.networking_v1 = client.NetworkingV1Api(self.api_client)
        self.autoscaling_v2 = client.AutoscalingV2Api(self.api_client)

    def fetch(
        self,
        namespace: str | None = None,
        exclude: set[str] | None = None,
    ) -> Generator[RawResource, None, None]:
        """Yield raw dicts for all supported resource kinds.

        Scopes to namespace if given, otherwise fetches the full cluster.
        Injects the kind string on each item because the k8s list API returns kind=None.
        Skips any resource whose namespace (or, for Namespace nodes, whose name) is in exclude.
        """
        for client_name, namespaced_method, cluster_method, kind in StaticIngestor.calls:
            api = getattr(self, client_name)
            if namespace and namespaced_method:
                method = getattr(api, namespaced_method)
                args = (namespace,)
            else:
                method = getattr(api, cluster_method)
                args = ()
            for item in method(*args).items:
                raw = item.to_dict()
                raw["kind"] = kind
                if exclude and _is_excluded(kind, raw, exclude):
                    continue
                yield raw
