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

# Each tuple: (api client attr, namespaced list method, cluster-wide list method, kind string to inject).
# Kind must be injected because the k8s list API always returns kind=None on items.
API_CALLS: list[tuple[str, str, str, str]] = [
    ("v1", "list_namespaced_pod", "list_pod_for_all_namespaces", "Pod"),
    ("apps_v1", "list_namespaced_deployment", "list_deployment_for_all_namespaces", "Deployment"),
    ("apps_v1", "list_namespaced_replica_set", "list_replica_set_for_all_namespaces", "ReplicaSet"),
    ("apps_v1", "list_namespaced_stateful_set", "list_stateful_set_for_all_namespaces", "StatefulSet"),
    ("apps_v1", "list_namespaced_daemon_set", "list_daemon_set_for_all_namespaces", "DaemonSet"),
]

# Kubeconfig resolution
#
# Priority:
#   1. Explicit --kubeconfig flag
#   2. KUBECONFIG environment variable
#   3. ~/.kube/config
#   4. Error
class StaticIngestor:
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

    def fetch(self, namespace: str | None = None) -> Generator[RawResource, None, None]:
        """Yield raw dicts for all supported resource kinds.

        Scopes to namespace if given, otherwise fetches the full cluster.
        Injects the kind string on each item because the k8s list API returns kind=None.
        """
        for client_name, namespaced_method, cluster_method, kind in API_CALLS:
            api = getattr(self, client_name)
            method = getattr(api, namespaced_method if namespace else cluster_method)
            call_args = (namespace,) if namespace else ()
            for item in method(*call_args).items:
                raw_json = item.to_dict()
                raw_json["kind"] = kind
                yield raw_json
