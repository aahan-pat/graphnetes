from enum import Enum


class ResourceKind(str, Enum):
    # Workloads
    POD = "Pod"
    CONTAINER = "Container"
    DEPLOYMENT = "Deployment"
    STATEFUL_SET = "StatefulSet"
    DAEMON_SET = "DaemonSet"
    REPLICA_SET = "ReplicaSet"
    JOB = "Job"
    CRON_JOB = "CronJob"

    # Networking
    SERVICE = "Service"
    INGRESS = "Ingress"
    NETWORK_POLICY = "NetworkPolicy"
    ENDPOINT_SLICE = "EndpointSlice"

    # Config
    CONFIG_MAP = "ConfigMap"
    SECRET = "Secret"

    # Storage
    PERSISTENT_VOLUME = "PersistentVolume"
    PERSISTENT_VOLUME_CLAIM = "PersistentVolumeClaim"
    STORAGE_CLASS = "StorageClass"

    # Identity & RBAC
    SERVICE_ACCOUNT = "ServiceAccount"
    ROLE = "Role"
    CLUSTER_ROLE = "ClusterRole"
    ROLE_BINDING = "RoleBinding"
    CLUSTER_ROLE_BINDING = "ClusterRoleBinding"

    # Infrastructure
    NODE = "Node"
    NAMESPACE = "Namespace"
    CLUSTER = "Cluster"

    # Scaling & availability
    HORIZONTAL_POD_AUTOSCALER = "HorizontalPodAutoscaler"
    VERTICAL_POD_AUTOSCALER = "VerticalPodAutoscaler"
    POD_DISRUPTION_BUDGET = "PodDisruptionBudget"

    # Extensibility
    CUSTOM_RESOURCE_DEFINITION = "CustomResourceDefinition"
    CUSTOM_RESOURCE = "CustomResource"

    # Declarative configuration snapshot derived from the last-applied annotation.
    MANIFEST = "Manifest"

    UNKNOWN = "Unknown"

    @classmethod
    def from_str(cls, value: str) -> "ResourceKind":
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN
