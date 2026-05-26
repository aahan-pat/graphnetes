from .static import StaticIngestor

# Kind must be injected because the k8s list API always returns kind=None on items.
StaticIngestor.register("v1", "list_namespaced_pod", "list_pod_for_all_namespaces", "Pod")
StaticIngestor.register("apps_v1", "list_namespaced_deployment", "list_deployment_for_all_namespaces", "Deployment")
StaticIngestor.register("apps_v1", "list_namespaced_replica_set", "list_replica_set_for_all_namespaces", "ReplicaSet")
StaticIngestor.register("apps_v1", "list_namespaced_stateful_set", "list_stateful_set_for_all_namespaces", "StatefulSet")
StaticIngestor.register("apps_v1", "list_namespaced_daemon_set", "list_daemon_set_for_all_namespaces", "DaemonSet")

__all__ = ["StaticIngestor"]
