# Stage 3: Networking, Config, Storage, and Infrastructure

Stage 3 fills the stub nodes left by Stages 1 and 2. Every `in_namespace`, `scheduled_on`,
`uses_service_account`, and `mounts` edge currently points at a node that was never ingested.
This stage ingests those target kinds — plus Service, Ingress, and HPA — so the graph has no
phantom nodes for common cluster resources.

---

## Part 1: Config and Identity

### ConfigMap

A ConfigMap holds arbitrary key-value configuration data decoupled from Pod specs. Pods
mount ConfigMaps as volumes or consume them as environment variables.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.annotations` | Node metadata |
| `data` | Key names only — stored as a list, never values |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `in_namespace` | ConfigMap | Namespace | `metadata.namespace` |

> Do not store ConfigMap values in node metadata. Values frequently contain credentials or
> other sensitive data.

---

### Secret

A Secret holds sensitive data such as passwords, tokens, and TLS certificates. Identical
structure to ConfigMap at the API level; the difference is the `type` field and that values
must never be stored.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.annotations` | Node metadata |
| `type` | Node metadata (e.g. `kubernetes.io/tls`, `Opaque`) |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `in_namespace` | Secret | Namespace | `metadata.namespace` |

> Never store `data` or `string_data` in node metadata.

---

### ServiceAccount

A ServiceAccount is a namespaced identity for processes running inside Pods. Pods reference
one via `spec.serviceAccountName`; Stage 2 already emits `uses_service_account` edges that
point at these nodes.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.annotations` | Node metadata |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `in_namespace` | ServiceAccount | Namespace | `metadata.namespace` |

---

## Part 2: Infrastructure

### Namespace

A Namespace is a cluster-scoped resource that partitions the cluster into virtual segments.
It is the target of every `in_namespace` edge already in the graph. No edges are emitted
from a Namespace node.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.labels` | Node metadata |
| `metadata.annotations` | Node metadata |
| `status.phase` | Node metadata (Active / Terminating) |

**Edges produced:** None. Namespace is always the target, never the source.

---

### Node

A Kubernetes Node is a worker machine. It is the target of every `scheduled_on` edge already
in the graph. Cluster-scoped — no namespace.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.labels` | Node metadata (includes topology labels e.g. `topology.kubernetes.io/zone`) |
| `metadata.annotations` | Node metadata |
| `status.conditions` | Node metadata (Ready, MemoryPressure, DiskPressure) |
| `status.allocatable` | Node metadata (cpu, memory) |

**Edges produced:** None. Node is always the target of `scheduled_on`, never the source.

---

## Part 3: Storage

### PersistentVolume

A PersistentVolume (PV) is a cluster-scoped storage resource provisioned by an administrator
or dynamically by a StorageClass. It is the target of `bound_to` edges from PVCs.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.labels` | Node metadata |
| `metadata.annotations` | Node metadata |
| `spec.capacity` | Node metadata |
| `spec.access_modes` | Node metadata |
| `spec.storage_class_name` | Node metadata |
| `spec.persistent_volume_reclaim_policy` | Node metadata |

**Edges produced:** None. PV is always the target of `bound_to`.

---

### PersistentVolumeClaim

A PersistentVolumeClaim (PVC) is a namespaced request for storage. It binds to a PV.
Stage 2 already emits `mounts` edges from StatefulSets and Pods that point at these nodes.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.annotations` | Node metadata |
| `spec.volume_name` | `bound_to` edge → PV |
| `spec.storage_class_name` | Node metadata |
| `status.phase` | Node metadata (Bound / Pending / Lost) |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `bound_to` | PVC | PV | `spec.volumeName` |
| `in_namespace` | PVC | Namespace | `metadata.namespace` |

---

## Part 4: Networking

### Service

A Service exposes a set of Pods under a stable DNS name and IP. It selects Pods via a flat
label selector on `spec.selector` — unlike Deployment selectors, this is not a `matchLabels`
object but a plain `dict[str, str]`.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.annotations` | Node metadata |
| `spec.selector` | `selects` edges → Pods (post-processing pass) |
| `spec.type` | Node metadata (ClusterIP / NodePort / LoadBalancer) |
| `spec.cluster_ip` | Node metadata |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `selects` | Service | Pod | `spec.selector` matched against Pod labels |
| `in_namespace` | Service | Namespace | `metadata.namespace` |

---

### Ingress

An Ingress routes external HTTP/HTTPS traffic to Services based on hostname and path rules.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.annotations` | Node metadata |
| `spec.rules[].http.paths[].backend.service.name` | `routes_to` edge → Service |
| `spec.default_backend.service.name` | `routes_to` edge → Service (fallback rule) |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `routes_to` | Ingress | Service | `spec.rules[].http.paths[].backend.service.name` |
| `routes_to` | Ingress | Service | `spec.defaultBackend.service.name` |
| `in_namespace` | Ingress | Namespace | `metadata.namespace` |

---

## Part 5: Scaling

### HorizontalPodAutoscaler

An HPA automatically scales the replica count of a target workload based on observed metrics.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.annotations` | Node metadata |
| `spec.scale_target_ref.kind` | `scales` edge — identifies target kind |
| `spec.scale_target_ref.name` | `scales` edge — identifies target name |
| `spec.min_replicas` | Node metadata |
| `spec.max_replicas` | Node metadata |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `scales` | HPA | Deployment / StatefulSet | `spec.scaleTargetRef` |
| `in_namespace` | HPA | Namespace | `metadata.namespace` |

---

## Service Selector Matching

Service selector matching extends the existing `build_selector_edges` pass in `GraphBuilder`.
Unlike controller selectors (`spec.selector.matchLabels`), a Service selector is a plain
`dict[str, str]` stored directly on `spec.selector` — there is no `matchLabels` wrapper.

The selector stored in the Service node's metadata must therefore be keyed separately from
controller selectors so `build_selector_edges` can distinguish the two and apply the correct
matching logic.

The matching rule is identical regardless of source: `selector.items() <= pod.labels.items()`.

---

## New API Clients

| Client | New kinds |
|---|---|
| `CoreV1Api` (already instantiated) | ConfigMap, Secret, ServiceAccount, Namespace, Node, PersistentVolume, PersistentVolumeClaim |
| `NetworkingV1Api` | Ingress |
| `AutoscalingV2Api` | HorizontalPodAutoscaler |

`NetworkingV1Api` and `AutoscalingV2Api` must be instantiated in `StaticIngestor.__init__`
alongside the existing `v1` and `apps_v1` clients, and registered as `networking_v1` and
`autoscaling_v2` attributes so `fetch` can resolve them by name.

---

## Implementation Order

1. Instantiate `NetworkingV1Api` and `AutoscalingV2Api` in `StaticIngestor.__init__`.
2. Register all new API calls in `ingest/__init__.py`.
3. Implement extractors for ConfigMap, Secret, ServiceAccount, Namespace, Node, PersistentVolume, PersistentVolumeClaim, Ingress, HPA.
4. Extend `build_selector_edges` in `GraphBuilder` to include Service nodes.
5. Register all new extractors via `@ExtractorRegistry.register`.

---

## Limitations

- Ingress `routes_to` edges resolve to Service names within the same namespace. Cross-namespace
  backends are not supported in standard Kubernetes Ingress — no special handling needed.
- HPA targets are resolved by name and namespace. If the target kind is not Deployment or
  StatefulSet (e.g. a custom CRD), the target node will remain a stub.
- Secret data is never stored. This means `mounts` edges to Secrets exist but Secret nodes
  carry no content metadata — intentional.
- Node and Namespace have no `in_namespace` edge of their own as they are cluster-scoped.
