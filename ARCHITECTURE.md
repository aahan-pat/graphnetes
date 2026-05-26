# Architecture

Graphnetes is a knowledge graph engine for Kubernetes clusters. It turns a live cluster into a queryable directed graph — every resource is a node, every relationship is a typed edge — and exposes that graph to humans via a CLI.

---

## Package Layout

```
graphnetes/
├── models/       # Core data types shared across all layers
├── ingest/       # Fetch raw resource dicts from the k8s API
├── extract/      # Convert resource dicts → ResourceNode + ResourceEdge
├── build/        # Construct and maintain the NetworkX DiGraph + indexes
├── export/       # Write graph.json and graph.html
└── cli/          # Typer CLI entry point and subcommands
    └── commands/
pyproject.toml    # Build config; installed script: graphnetes = graphnetes.cli.app:app
```

Dev entry point: `python -m graphnetes <command>`

---

## Data Flow

```
[k8s API]
    │
 ingest/        raw dicts (point-in-time snapshot)
    │
 extract/       ResourceNode, ResourceEdge
    │
 build/         NetworkX DiGraph + kind/namespace indexes
    │
 export/        graph.json  ·  graph.html
    │
 cli/           subcommands (human interface)
```

---

## Models (`graphnetes/models/`)

Shared data types used at every layer.

### `ResourceNode`

Represents a single Kubernetes resource.

| Field | Type | Description |
|---|---|---|
| `id` | `str` | `"{kind}/{namespace}/{name}"` or `"{kind}/{name}"` for cluster-scoped |
| `kind` | `ResourceKind` | Enum of all supported resource kinds |
| `name` | `str` | Resource name |
| `namespace` | `str \| None` | `None` for cluster-scoped resources |
| `labels` | `dict[str, str]` | Resource labels |
| `annotations` | `dict[str, str]` | Resource annotations |
| `metadata` | `dict[str, Any]` | Arbitrary resource-specific fields |

### `ResourceEdge`

Represents a typed, directed relationship between two nodes.

| Field | Type | Description |
|---|---|---|
| `source_id` | `str` | ID of the source node |
| `target_id` | `str` | ID of the target node |
| `relation` | `EdgeRelation` | The relationship type |
| `confidence` | `Confidence` | EXTRACTED / INFERRED / AMBIGUOUS |
| `confidence_score` | `float` | 0.0–1.0; EXTRACTED is always 1.0 |
| `weight` | `float` | Edge weight for traversal algorithms |
| `metadata` | `dict[str, Any]` | Arbitrary edge fields |

### `ResourceKind`

`str` enum of every supported Kubernetes resource kind, grouped by category:

| Category | Kinds |
|---|---|
| Workloads | Pod, Container, Deployment, StatefulSet, DaemonSet, ReplicaSet, Job, CronJob |
| Networking | Service, Ingress, NetworkPolicy, EndpointSlice |
| Config | ConfigMap, Secret |
| Storage | PersistentVolume, PersistentVolumeClaim, StorageClass |
| Identity & RBAC | ServiceAccount, Role, ClusterRole, RoleBinding, ClusterRoleBinding |
| Infrastructure | Node, Namespace, Cluster |
| Scaling | HorizontalPodAutoscaler, VerticalPodAutoscaler, PodDisruptionBudget |
| Extensibility | CustomResourceDefinition, CustomResource |

Unknown kinds resolve to `ResourceKind.UNKNOWN` via `ResourceKind.from_str()`.

### `EdgeRelation`

`str` enum of all typed edge relationships:

| Relation | Direction | Source | Target | How Derived |
|---|---|---|---|---|
| `owns` | → | Deployment / ReplicaSet / Job | ReplicaSet / Pod | `ownerReferences` |
| `selects` | → | Deployment / ReplicaSet / StatefulSet / DaemonSet / Service | Pod | label selector match (post-processing pass) |
| `routes_to` | → | Ingress | Service | `spec.rules[].backend` |
| `mounts` | → | Pod | ConfigMap / Secret / PVC | `volumes[]` |
| `uses_service_account` | → | Pod | ServiceAccount | `spec.serviceAccountName` |
| `scheduled_on` | → | Pod | Node | `spec.nodeName` |
| `applies_to` | → | NetworkPolicy | Pod | pod selector match |
| `scales` | → | HPA | Deployment / StatefulSet | `spec.scaleTargetRef` |
| `bound_to` | → | PVC | PV | `spec.volumeName` |
| `in_namespace` | → | any namespaced resource | Namespace | `metadata.namespace` |
| `communicates_with` | ↔ | Pod | Pod | inferred from NetworkPolicy allow rules |
| `grants` | → | RoleBinding / ClusterRoleBinding | Role + ServiceAccount | `subjects[]` + `roleRef` |
| `configured_by` | → | resource | manifest snapshot | last-applied annotation |

### `Confidence`

`str` enum describing how an edge was derived:

| Value | Meaning |
|---|---|
| `EXTRACTED` | Directly read from the resource spec; `confidence_score` is always 1.0 |
| `INFERRED` | Resolved via selector matching or owner chains |
| `AMBIGUOUS` | Uncertain; multiple possible interpretations |

---

## Modules

### `ingest/`

Takes a point-in-time snapshot of all resources from a live cluster via the official `kubernetes` Python client.

`StaticIngestor` connects to a cluster, iterates over every registered API call, and yields raw resource dicts. Kind strings are injected on each item because the k8s list API always returns `kind=None` on list items.

API calls are registered in `ingest/register.py` via `StaticIngestor.register(client, namespaced_method, cluster_method, kind)`. Currently registered:

| API group | Kinds |
|---|---|
| `CoreV1Api` | Pod, Namespace, Node, PersistentVolume, Service, Secret, ConfigMap, ServiceAccount, PersistentVolumeClaim |
| `AppsV1Api` | Deployment, ReplicaSet, StatefulSet, DaemonSet |
| `NetworkingV1Api` | Ingress |
| `AutoscalingV2Api` | HorizontalPodAutoscaler |

`ingest/live.py` defines the interface for streaming watch events (ADDED / MODIFIED / DELETED) but is not yet implemented.

### `extract/`

Converts raw resource dicts into `ResourceNode` and `ResourceEdge` objects. Each resource kind has a dedicated extractor function registered via `@ExtractorRegistry.register("Kind")`. Extractors read relevant spec fields and emit edges with the appropriate `EdgeRelation` and `Confidence`.

Extractor files:

| File | Kinds |
|---|---|
| `workloads.py` | Pod, Deployment, ReplicaSet, StatefulSet, DaemonSet |
| `networking.py` | Service, Ingress |
| `config.py` | ConfigMap, Secret, ServiceAccount |
| `storage.py` | PersistentVolume, PersistentVolumeClaim |
| `infrastructure.py` | Node, Namespace |

`SELECTS` edges are not emitted by extractors. They are resolved in a post-processing pass in `build/` after all nodes are loaded.

### `build/`

`GraphBuilder` wraps a `networkx.DiGraph` and maintains two in-memory indexes:

- `_kind_index` — keyed by `(kind, namespace, name)` for O(1) node lookup
- `_namespace_index` — keyed by namespace, maps to a list of node IDs

After all nodes and extracted edges are added, `build_selector_edges()` runs a post-processing pass: for each controller kind (Deployment, ReplicaSet, StatefulSet, DaemonSet, Service) it matches label selectors against all Pods and adds `SELECTS` edges with `confidence=INFERRED`.

`GraphBuilder.load(path)` reconstructs the full graph from a `graph.json` file without re-connecting to the cluster.

`shortest_path(source_id, target_id)` delegates to `networkx.shortest_path` and returns the `ResourceNode` objects along the path.

### `export/`

Serializes the built graph to the output directory. Two formats are produced:

| File | Format |
|---|---|
| `graph.json` | NetworkX node-link JSON — primary persistent format, used by all query commands |
| `graph.html` | Self-contained interactive browser visualization |

Nodes that appear as edge targets but were never ingested (e.g. a Namespace referenced by an `in_namespace` edge before Namespace objects are loaded) become attribute-less stubs in NetworkX. The exporter detects these and synthesises minimal node dicts from the ID string so the visualizer can still render the edge.

### `cli/`

Typer app registered at `graphnetes.cli.app:app`.

| Command | Module | Description |
|---|---|---|
| `build` | `commands/build.py` | Connect to cluster, build graph, write output files |
| `path <source> <target>` | `commands/path.py` | Shortest path between two nodes |
| `inspect <node-id>` | `commands/inspect.py` | Full node details and all edges |
| `neighbors <node-id>` | `commands/neighbors.py` | Direct neighbors, filterable by direction |
| `list <kind>` | `commands/list_nodes.py` | All nodes of a given kind, filterable by namespace |

`commands/_parse.py` holds shared helpers used by the query commands: `load_graph`, `resolve_node`, and `collect_edges`.

---

## Key Dependencies

| Library | Role |
|---|---|
| `networkx` | Graph construction, BFS/DFS, shortest path |
| `kubernetes` | Official Python k8s API client |
| `typer` | CLI |
| `rich` | Terminal output formatting |
