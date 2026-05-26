from enum import Enum


class EdgeRelation(str, Enum):
    # Derived from ownerReferences, e.g. Deployment owns ReplicaSet owns Pod.
    OWNS = "owns"
    # Derived from a labelSelector match, e.g. a Service or Deployment selecting Pods.
    SELECTS = "selects"
    # An Ingress routing traffic to a Service.
    ROUTES_TO = "routes_to"
    # A Pod mounting a ConfigMap, Secret, or PersistentVolumeClaim.
    MOUNTS = "mounts"
    # A Pod bound to a ServiceAccount.
    USES_SERVICE_ACCOUNT = "uses_service_account"
    # A Pod scheduled onto a Node.
    SCHEDULED_ON = "scheduled_on"
    # A NetworkPolicy applying to a set of Pods.
    APPLIES_TO = "applies_to"
    # An HorizontalPodAutoscaler scaling a Deployment or StatefulSet.
    SCALES = "scales"
    # A PersistentVolumeClaim bound to a PersistentVolume.
    BOUND_TO = "bound_to"
    # A namespaced resource belonging to a Namespace.
    IN_NAMESPACE = "in_namespace"
    # Inferred from NetworkPolicy allow rules between workloads.
    COMMUNICATES_WITH = "communicates_with"
    # A RoleBinding granting a Role to a ServiceAccount.
    GRANTS = "grants"
    # A resource whose configuration was last applied from a manifest snapshot.
    CONFIGURED_BY = "configured_by"
