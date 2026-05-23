from enum import Enum


class EdgeRelation(str, Enum):
    # ownerReferences (Deployment → ReplicaSet → Pod)
    OWNS = "owns"
    # labelSelector match (Service/Deployment → Pod)
    SELECTS = "selects"
    # Ingress → Service
    ROUTES_TO = "routes_to"
    # Pod mounts ConfigMap / Secret / PVC
    MOUNTS = "mounts"
    # Pod → ServiceAccount
    USES_SERVICE_ACCOUNT = "uses_service_account"
    # Pod → Node
    SCHEDULED_ON = "scheduled_on"
    # NetworkPolicy → Pod
    APPLIES_TO = "applies_to"
    # HPA → Deployment / StatefulSet
    SCALES = "scales"
    # PVC → PV
    BOUND_TO = "bound_to"
    # Namespaced resource → Namespace
    IN_NAMESPACE = "in_namespace"
    # Inferred from NetworkPolicy allow rules
    COMMUNICATES_WITH = "communicates_with"
    # RoleBinding → Role + ServiceAccount
    GRANTS = "grants"
