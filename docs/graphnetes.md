# Graphnetes

A knowledge graph engine for Kubernetes clusters, designed for fast traversal and agent-driven exploration.

---

## Overview

Graphnetes turns a live or static Kubernetes cluster into a queryable knowledge graph. Every resource becomes a node; every relationship (ownership, selection, mounting, routing) becomes a typed edge. The resulting graph answers questions that `kubectl` cannot:

- What breaks if I delete this Deployment?
- Which pods can communicate with the payments namespace?
- What does this Ingress ultimately route to?
- Which ServiceAccounts have cluster-admin privileges?
- Are there any Services with no pods behind them?

The graph is designed to be consumed by AI agents via an MCP server, and by humans via a CLI and browser-based visualization.

---

## Node Types

Every Kubernetes resource kind is a first-class node:

| Category | Kinds |
|---|---|
| Workloads | Pod, Container, Deployment, StatefulSet, DaemonSet, ReplicaSet, Job, CronJob |
| Networking | Service, Ingress, NetworkPolicy, EndpointSlice |
| Config | ConfigMap, Secret |
| Storage | PersistentVolume, PersistentVolumeClaim, StorageClass |
| Identity | ServiceAccount, Role, ClusterRole, RoleBinding, ClusterRoleBinding |
| Infrastructure | Node (worker), Namespace, Cluster |
| Scaling | HorizontalPodAutoscaler, VerticalPodAutoscaler, PodDisruptionBudget |
| Extensibility | CustomResourceDefinition, CRD instances |

Each node carries: `kind`, `name`, `namespace`, `labels`, `annotations`, and a `metadata` dict for arbitrary resource fields.

---

## Edge Types

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

Edges carry: `relation`, `confidence` (EXTRACTED / INFERRED / AMBIGUOUS), `confidence_score` (0.0–1.0), and `weight`.

---

## Data Sources

### Live Mode
Connects to a running cluster via the official `kubernetes` Python client. Fetches all resource kinds across namespaces (or a scoped namespace). Supports async watch for incremental, real-time graph updates as resources are created, modified, or deleted.

### Static Mode
Parses local files without a live cluster:
- YAML manifests (single file or directory tree)
- `kubectl get all -o json` output
- Helm chart rendered templates (`helm template`)

---

## Architecture

```
graphnetes/
├── ingest/     # Fetch raw resource dicts from k8s API or YAML files
├── extract/    # Convert resource dicts → ResourceNode + ResourceEdge objects
├── build/      # Construct and maintain the NetworkX DiGraph; namespace/kind indexes
├── analyze/    # BFS/DFS traversal, shortest path, blast radius, anomaly detection
├── query/      # Dispatch natural-language questions over graph structure
├── export/     # graph.json, HTML visualization, GraphML, Cypher (Neo4j)
├── serve/      # MCP stdio server — exposes graph as agent tools
└── cli/        # Typer CLI entry point
```

### Data Flow

```
[k8s API / YAML]
      │
   ingest/          ← raw dicts
      │
   extract/         ← ResourceNode, ResourceEdge
      │
   build/           ← NetworkX DiGraph + indexes
      │
   ┌──┴──┐
analyze/ export/    ← analysis results, graph.json, graph.html
   └──┬──┘
   serve/           ← MCP tools (agent interface)
   cli/             ← human interface
```

---

## Performance Strategy

| Concern | Approach |
|---|---|
| Graph engine | NetworkX DiGraph (default); `python-igraph` as opt-in fast backend for clusters > 10k nodes |
| Resource lookup | In-memory index keyed by `(kind, namespace, name)` — O(1) |
| Path computation | `functools.lru_cache` on `shortest_path` results; cache invalidated on graph update |
| Ingestion | Async `kubernetes` client + `asyncio` for live mode; multiprocessing for large YAML corpora |
| Incremental updates | K8s watch events (ADDED / MODIFIED / DELETED) patch the graph without full rebuild |
| Subgraph queries | Namespace-scoped subgraphs precomputed and cached on first access |

---

## Agent Interface (MCP Tools)

Graphnetes exposes an MCP stdio server so agents can query the graph without file I/O.

| Tool | Description |
|---|---|
| `query_graph(question, mode, depth)` | BFS or DFS traversal driven by natural-language question |
| `get_resource(kind, name, namespace)` | Full node details + metadata |
| `get_neighbors(kind, name, namespace, direction)` | Adjacent nodes (in / out / both) |
| `find_path(source, target)` | Shortest path between two resources |
| `blast_radius(kind, name, namespace)` | All resources that depend on this one (reverse BFS) |
| `dependency_tree(kind, name, namespace)` | All resources this one depends on (forward BFS) |
| `get_namespace_graph(namespace)` | Subgraph scoped to a single namespace |
| `graph_stats()` | Node count, edge count, density, breakdown by kind |
| `anomalies()` | Orphaned Services, Pods without selectors, unbound PVCs, etc. |
| `explain_resource(kind, name, namespace)` | Full context: neighbors, edge relations, community |

---

## CLI

```
graphnetes build                             # build from current kubeconfig
graphnetes build --context prod --namespace payments
graphnetes build --from-file manifests/      # build from local YAML

graphnetes query "what depends on redis?"
graphnetes path deploy/frontend svc/backend
graphnetes blast-radius deploy/payments
graphnetes anomalies

graphnetes serve --mcp                       # start MCP stdio server
graphnetes viz                               # open graph.html in browser
```

---

## Key Libraries

| Library | Role |
|---|---|
| `networkx` | Graph construction, BFS/DFS, shortest path |
| `kubernetes` | Official Python k8s API client (sync + async) |
| `typer` | CLI |
| `rich` | Terminal output formatting |
| `mcp` | MCP server protocol |
| `pyyaml` | YAML manifest parsing |
| `python-igraph` | Optional fast graph backend for large clusters |

---

## Output Files

```
graphnetes-out/
├── graph.json      # Persistent NetworkX node-link JSON (survives sessions)
├── graph.html      # Interactive browser visualization (no server needed)
├── graph.graphml   # (optional) Gephi / yEd export
└── cypher.txt      # (optional) Neo4j Cypher import script
```

---

## Example Agent Use Cases

```
"What services would go down if I delete the redis Deployment in prod?"
→ blast_radius(kind="Deployment", name="redis", namespace="prod")

"Show me all pods that can talk to the payments namespace."
→ query_graph("pods communicating with payments namespace")

"Which ServiceAccounts have cluster-admin privileges?"
→ query_graph("ServiceAccounts with cluster-admin", mode="dfs", depth=4)

"Trace the path from the frontend Ingress to the database Pod."
→ find_path("Ingress/frontend", "Pod/postgres-0")

"Are there any Services with no pods behind them?"
→ anomalies()

"What does the auth Deployment depend on?"
→ dependency_tree(kind="Deployment", name="auth", namespace="default")
```
