"""
Static ingestion — connects to a cluster and takes a one-time snapshot of all resources.

Fetches every supported resource kind across the cluster (or a single namespace)
and returns raw resource dicts. No watch; the graph reflects the cluster state
at the moment of the call.
"""

import os
from pathlib import Path
from typing import Any, Generator, Optional

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


RawResource = dict[str, Any]

_DEFAULT_KUBECONFIG = Path.home() / ".kube" / "config"


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
        kubeconfig: Optional[str] = None,
        context: Optional[str] = None,
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

        elif _DEFAULT_KUBECONFIG.exists():
            config.load_kube_config(
                config_file=str(_DEFAULT_KUBECONFIG),
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

    # Fetching
    def fetch_namespace(self, namespace: str) -> Generator[RawResource, None, None]:
        """Yield raw resource dicts for all resources in a single namespace."""
        for pod in self.v1.list_namespaced_pod(namespace):
            yield pod.to_dict()

    def fetch_cluster(self) -> Generator[RawResource, None, None]:
        """Yield raw resource dicts for all resources across every namespace in the cluster."""
        for pod in self.v1.list_pod_for_all_namespaces(watch=False).items:
            yield pod.to_dict()

    def fetch(self, namespace: Optional[str] = None) -> Generator[RawResource, None, None]:
        """
        Main entry point. Scopes to namespace if given, otherwise fetches the full cluster.
        """
        if namespace:
            yield from self.fetch_namespace(namespace)
        else:
            yield from self.fetch_cluster()
