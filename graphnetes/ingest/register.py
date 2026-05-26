# Kind must be injected because the k8s list API always returns kind=None on items.
from graphnetes.ingest.static import StaticIngestor

# Stage 1: Pods
StaticIngestor.register("v1", "list_namespaced_pod", "list_pod_for_all_namespaces", "Pod")
StaticIngestor.register("v1", None, "list_namespace", "Namespace")
StaticIngestor.register("v1", None, "list_node", "Node")
StaticIngestor.register("v1", None, "list_persistent_volume", "PersistentVolume")

# Stage 2: Workload controllers
StaticIngestor.register("apps_v1", "list_namespaced_deployment", "list_deployment_for_all_namespaces", "Deployment")
StaticIngestor.register("apps_v1", "list_namespaced_replica_set", "list_replica_set_for_all_namespaces", "ReplicaSet")
StaticIngestor.register("apps_v1", "list_namespaced_stateful_set", "list_stateful_set_for_all_namespaces", "StatefulSet")
StaticIngestor.register("apps_v1", "list_namespaced_daemon_set", "list_daemon_set_for_all_namespaces", "DaemonSet")

# Stage 3: Networking, config, storage, and infrastructure kinds
StaticIngestor.register("v1", "list_namespaced_service", "list_service_for_all_namespaces", "Service")
StaticIngestor.register("v1", "list_namespaced_secret", "list_secret_for_all_namespaces", "Secret")
StaticIngestor.register("v1", "list_namespaced_config_map", "list_config_map_for_all_namespaces", "ConfigMap")
StaticIngestor.register("v1", "list_namespaced_service_account", "list_service_account_for_all_namespaces", "ServiceAccount")
StaticIngestor.register("v1", "list_namespaced_persistent_volume_claim", "list_persistent_volume_claim_for_all_namespaces", "PersistentVolumeClaim")
StaticIngestor.register("networking_v1", "list_namespaced_ingress", "list_ingress_for_all_namespaces", "Ingress")
StaticIngestor.register("autoscaling_v2", "list_namespaced_horizontal_pod_autoscaler", "list_horizontal_pod_autoscaler_for_all_namespaces", "HorizontalPodAutoscaler")
