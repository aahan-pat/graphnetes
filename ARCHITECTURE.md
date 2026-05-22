# Architecture

Graphnetes is a knowledge graph engine for Kubernetes clusters. It turns a live or static cluster into a queryable directed graph — every resource is a node, every relationship is a typed edge — and exposes that graph to humans via a CLI and to AI agents via an MCP stdio server.

---

## Package Layout

```
graphnetes/
├── models/       # Core data types shared across all layers
├── ingest/       # Fetch raw resource dicts from k8s API or YAML files
├── extract/      # Convert resource dicts → ResourceNode + ResourceEdge
├── build/        # Construct and maintain the NetworkX DiGraph + indexes
├── analyze/      # BFS/DFS traversal, shortest path, blast radius, anomaly detection
├── query/        # Dispatch natural-language questions over graph structure
├── export/       # Serialize graph to JSON, HTML, GraphML, Cypher
├── serve/        # MCP stdio server — exposes graph as agent tools
└── cli/          # Typer CLI entry point and subcommands
    └── commands/
main.py           # Dev entry point (python main.py <command>)
pyproject.toml    # Build config; installed script: graphnetes = graphnetes.cli.app:app
```

---

## Data Flow

```
[k8s API / YAML files]
        │
     ingest/          raw dicts
        │
     extract/         ResourceNode, ResourceEdge
        │
     build/           NetworkX DiGraph + kind/namespace indexes
        │
   ┌────┴────┐
analyze/  export/     analysis results · graph.json · graph.html
   └────┬────┘
     serve/           MCP tools  (agent interface)
      cli/            subcommands (human interface)
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
| `metadata` | `dict[str, Any]` | Arbitrary resource fields |

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
| `selects` | → | Service / Deployment | Pod | label selector match |
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

Fetches raw Kubernetes resource dicts. Two modes:

- **Live** — connects to a running cluster via the official `kubernetes` Python client; supports async watch for incremental real-time updates (ADDED / MODIFIED / DELETED events).
- **Static** — parses local YAML manifests (single file or directory tree), `kubectl get all -o json` output, or Helm rendered templates.

### `extract/`

Converts raw resource dicts into `ResourceNode` and `ResourceEdge` objects. One extractor per resource kind; each reads the relevant spec fields and emits edges with the appropriate `EdgeRelation` and `Confidence`.

### `build/`

Constructs and maintains a `networkx.DiGraph`. Maintains two in-memory indexes for O(1) lookup:
- by `(kind, namespace, name)`
- by namespace (for subgraph queries)

Applies incremental patches from watch events without full rebuilds. Precomputes and caches namespace-scoped subgraphs on first access.

### `analyze/`

Graph traversal and analysis over the DiGraph:

| Operation | Description |
|---|---|
| BFS / DFS traversal | Configurable depth, direction (in / out / both) |
| Shortest path | `functools.lru_cache` on results; invalidated on graph update |
| Blast radius | Reverse BFS from a node — everything that depends on it |
| Dependency tree | Forward BFS from a node — everything it depends on |
| Anomaly detection | Orphaned Services, Pods without selectors, unbound PVCs, stale ReplicaSets |

### `query/`

Dispatches natural-language questions to `analyze/` traversal operations. Parses the question to identify the target resource kind, name, and traversal intent, then routes to the appropriate analysis call.

### `export/`

Serializes the graph to multiple output formats:

| File | Format |
|---|---|
| `graph.json` | NetworkX node-link JSON — primary persistent format |
| `graph.html` | Self-contained interactive browser visualization |
| `graph.graphml` | GraphML for Gephi / yEd |
| `cypher.txt` | Neo4j Cypher import script |

### `serve/`

MCP stdio server that exposes the graph as agent tools:

| Tool | Description |
|---|---|
| `query_graph(question, mode, depth)` | BFS or DFS traversal driven by a natural-language question |
| `get_resource(kind, name, namespace)` | Full node details and metadata |
| `get_neighbors(kind, name, namespace, direction)` | Adjacent nodes (in / out / both) |
| `find_path(source, target)` | Shortest path between two resources |
| `blast_radius(kind, name, namespace)` | All resources that depend on this one |
| `dependency_tree(kind, name, namespace)` | All resources this one depends on |
| `get_namespace_graph(namespace)` | Subgraph scoped to a single namespace |
| `graph_stats()` | Node count, edge count, density, breakdown by kind |
| `anomalies()` | Orphaned Services, Pods without selectors, unbound PVCs, etc. |
| `explain_resource(kind, name, namespace)` | Full context: neighbors, edge relations, community |

### `cli/`

Typer CLI. Entry point: `graphnetes.cli.app:app` (installed script) or `python main.py` (dev).

| Command | Description |
|---|---|
| `graphnetes build` | Build graph from current kubeconfig or local YAML |
| `graphnetes query "<question>"` | Natural-language query over the graph |
| `graphnetes path <source> <target>` | Shortest path between two resources |
| `graphnetes blast-radius <resource>` | Show everything that breaks if this resource is deleted |
| `graphnetes anomalies` | Scan for graph-level anomalies |
| `graphnetes serve` | Start the MCP stdio server |
| `graphnetes viz` | Open `graph.html` in a browser |

---

## Performance

| Concern | Approach |
|---|---|
| Graph engine | NetworkX DiGraph (default); `python-igraph` as opt-in fast backend for clusters > 10k nodes |
| Resource lookup | In-memory index keyed by `(kind, namespace, name)` — O(1) |
| Path computation | `functools.lru_cache` on `shortest_path`; invalidated on graph update |
| Ingestion | Async `kubernetes` client + `asyncio` for live mode; multiprocessing for large YAML corpora |
| Incremental updates | K8s watch events patch the graph without full rebuild |
| Subgraph queries | Namespace-scoped subgraphs precomputed and cached on first access |

---

## Key Dependencies

| Library | Role |
|---|---|
| `networkx` | Graph construction, BFS/DFS, shortest path |
| `kubernetes` | Official Python k8s API client (sync + async) |
| `typer` | CLI |
| `rich` | Terminal output formatting |
| `mcp` | MCP server protocol |
| `pyyaml` | YAML manifest parsing |
| `python-igraph` | Optional fast graph backend for large clusters |
