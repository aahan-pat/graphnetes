from enum import Enum


class EdgeRelation(str, Enum):
    OWNS = "owns"                                       # ownerReferences (Deployment → ReplicaSet → Pod)
    SELECTS = "selects"                                 # labelSelector match (Service/Deployment → Pod)
    ROUTES_TO = "routes_to"                             # Ingress → Service
    MOUNTS = "mounts"                                   # Pod mounts ConfigMap / Secret / PVC
    USES_SERVICE_ACCOUNT = "uses_service_account"       # Pod → ServiceAccount
    SCHEDULED_ON = "scheduled_on"                       # Pod → Node
    APPLIES_TO = "applies_to"                           # NetworkPolicy → Pod
    SCALES = "scales"                                   # HPA → Deployment / StatefulSet
    BOUND_TO = "bound_to"                               # PVC → PV
    IN_NAMESPACE = "in_namespace"                       # namespaced resource → Namespace
    COMMUNICATES_WITH = "communicates_with"             # inferred from NetworkPolicy allow rules
    GRANTS = "grants"                                   # RoleBinding → Role + ServiceAccount
