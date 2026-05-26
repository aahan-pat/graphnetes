# Stage 2: Workload Controllers and Manifest Nodes

Stage 2 expands ingestion beyond Pods to cover the controllers that own them, and
introduces Manifest nodes that track how resources were declaratively applied.

---

## Part 1: Workload Controllers

### Resources to fetch

| Kind | Kubernetes API | API Group |
|---|---|---|
| Deployment | `list_deployment_for_all_namespaces` | `AppsV1Api` |
| ReplicaSet | `list_replica_set_for_all_namespaces` | `AppsV1Api` |
| StatefulSet | `list_stateful_set_for_all_namespaces` | `AppsV1Api` |
| DaemonSet | `list_daemon_set_for_all_namespaces` | `AppsV1Api` |

All four use `AppsV1Api`, which needs to be instantiated alongside the existing
`CoreV1Api` in `StaticIngestor`.

---

### Deployment

A Deployment manages a desired replica count of a stateless workload. It creates
and owns a ReplicaSet, which in turn owns the Pods.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.owner_references` | `owns` edge from any parent |
| `metadata.annotations` | Manifest node (last-applied-configuration) |
| `spec.selector.match_labels` | `selects` edges → Pods |
| `spec.replicas` | Node metadata |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `owns` | parent (if any) | Deployment | `ownerReferences` |
| `selects` | Deployment | Pod | `spec.selector.matchLabels` matched against Pod labels |
| `in_namespace` | Deployment | Namespace | `metadata.namespace` |
| `configured_by` | Deployment | Manifest | last-applied annotation |

---

### ReplicaSet

A ReplicaSet ensures N Pod replicas are running. Rarely created directly — Deployments
create them. Multiple ReplicaSets per Deployment can exist simultaneously during
a rolling update.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.owner_references` | `owns` edge from Deployment |
| `metadata.annotations` | Manifest node |
| `spec.selector.match_labels` | `selects` edges → Pods |
| `spec.replicas` | Node metadata |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `owns` | Deployment | ReplicaSet | `ownerReferences` on ReplicaSet |
| `selects` | ReplicaSet | Pod | `spec.selector.matchLabels` matched against Pod labels |
| `in_namespace` | ReplicaSet | Namespace | `metadata.namespace` |
| `configured_by` | ReplicaSet | Manifest | last-applied annotation |

---

### StatefulSet

A StatefulSet manages stateful workloads. Pods get stable, ordered names (`mysql-0`,
`mysql-1`) and each Pod gets its own PVC that persists across restarts.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.owner_references` | `owns` edge from any parent |
| `metadata.annotations` | Manifest node |
| `spec.selector.match_labels` | `selects` edges → Pods |
| `spec.replicas` | Node metadata |
| `spec.volume_claim_templates` | `mounts` edges → PVCs (one per replica) |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `owns` | parent (if any) | StatefulSet | `ownerReferences` |
| `selects` | StatefulSet | Pod | `spec.selector.matchLabels` matched against Pod labels |
| `mounts` | StatefulSet | PVC | `spec.volumeClaimTemplates[].metadata.name` |
| `in_namespace` | StatefulSet | Namespace | `metadata.namespace` |
| `configured_by` | StatefulSet | Manifest | last-applied annotation |

---

### DaemonSet

A DaemonSet ensures exactly one Pod runs on every Node (or a node subset). Used for
cluster-level agents: log collectors, monitoring exporters, CNI plugins.

**Fields to extract:**

| Field | Used for |
|---|---|
| `metadata.name` | Node identity |
| `metadata.namespace` | Node identity, `in_namespace` edge |
| `metadata.labels` | Node metadata |
| `metadata.owner_references` | `owns` edge from any parent |
| `metadata.annotations` | Manifest node |
| `spec.selector.match_labels` | `selects` edges → Pods |

**Edges produced:**

| Relation | Source | Target | How derived |
|---|---|---|---|
| `owns` | parent (if any) | DaemonSet | `ownerReferences` |
| `selects` | DaemonSet | Pod | `spec.selector.matchLabels` matched against Pod labels |
| `in_namespace` | DaemonSet | Namespace | `metadata.namespace` |
| `configured_by` | DaemonSet | Manifest | last-applied annotation |

---

### Label selector matching

`selects` edges for all four controllers are derived by matching `spec.selector.matchLabels`
against Pod labels. This cannot be done per-resource in isolation — it requires
access to the full set of ingested Pods. The match should run as a post-processing
pass in `GraphBuilder` after all nodes are added, not inside individual extractors.

```
for each controller node:
    for each pod node:
        if controller.selector ⊆ pod.labels:
            add selects edge
```

---

## Part 2: Manifest Nodes

### Background

When a resource is created or updated via `kubectl apply -f`, Kubernetes stores a
snapshot of the submitted manifest as an annotation on the resource:

```
kubectl.kubernetes.io/last-applied-configuration: '{"apiVersion":"apps/v1","kind":"Deployment",...}'
```

This is the only cluster-side record that a resource was declaratively managed.
Resources created imperatively (`kubectl run`, `kubectl create`) do not have it.

The annotation does **not** include the source filename. Identity must be derived
from the annotation content itself.

---

### What we can derive

| Data | How |
|---|---|
| Resource was declaratively managed | Annotation is present |
| Original spec at last apply | Parse annotation JSON |
| Divergence from live spec | Diff annotation against live `spec` — out of scope for Stage 2 |
| Shared manifest (multiple resources applied together) | Not derivable — no filename |

---

### Data model

**New `ResourceKind`:**

```python
MANIFEST = "Manifest"
```

**New `EdgeRelation`:**

```python
# A resource whose configuration was last applied from a manifest snapshot.
CONFIGURED_BY = "configured_by"
```

**Manifest node identity:**

Keyed by a SHA-256 hash of the annotation JSON, so two resources applied from the
same manifest content share a single Manifest node:

```
Manifest/<first-12-chars-of-sha256>
```

Node carries:
- `kind`: `Manifest`
- `name`: first 12 chars of SHA-256 hash
- `namespace`: `None` (cluster-scoped)
- `labels`: `{}`
- `metadata`: `{ "spec": <parsed annotation dict> }`

---

### Edge

```
Resource ──configured_by──▶ Manifest
```

Produced for any resource whose raw dict contains the annotation. Resources without
it produce no edge and no Manifest node.

---

### Extractor design

A shared helper on `BaseExtractor` handles the annotation for all resource types:

```python
def extract_manifest_edge(self, resource: RawResource, source_id: str) -> tuple[ResourceNode, ResourceEdge] | None:
    """Return a Manifest node and configured_by edge if the last-applied annotation is present."""
```

Returns `None` when the annotation is absent. Every extractor calls this and
appends the result if non-None — no per-extractor logic needed.

---

## Implementation Order

1. Add `AppsV1Api` to `StaticIngestor`; add fetch methods for all four controller kinds.
2. Add `MANIFEST = "Manifest"` to `ResourceKind` and `CONFIGURED_BY = "configured_by"` to `EdgeRelation`.
3. Implement `extract_manifest_edge` on `BaseExtractor`.
4. Implement `DeploymentExtractor`, `ReplicaSetExtractor`, `StatefulSetExtractor`, `DaemonSetExtractor`.
5. Add label selector matching pass to `GraphBuilder`.
6. Wire all four extractors into the `build` CLI command.
7. Add `Manifest` color entry to `KIND_COLORS` in `_template.py`.

---

## Limitations

- Label selector matching is O(controllers × pods) — acceptable for clusters up to
  tens of thousands of resources, but worth noting.
- Manifest nodes are only created for resources applied via `kubectl apply`. Helm
  creates them (it calls `kubectl apply` under the hood); ArgoCD and Flux typically
  do not.
- The last-applied annotation is truncated by Kubernetes if the manifest exceeds
  ~256 KB.
