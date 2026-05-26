# Graphnetes

A knowledge graph engine for Kubernetes clusters. Every resource becomes a node, every relationship becomes a typed edge allowing easy enumeration for any cluster. 

```
graphnetes build --context prod --namespace payments
graphnetes path Ingress/prod/frontend Pod/prod/payments-6d4f9b
graphnetes inspect Deployment/prod/payments
```

---

## What it does

Graphnetes connects to a live cluster, snapshots all resources, and builds a directed graph of how they relate to each other. You can then query that graph to understand dependencies, trace paths, and inspect individual resources — from the CLI or from an AI agent.

```
"Trace the path from the frontend Ingress to the database Pod."
"What does the payments Deployment select?"
"Which Services exist in the prod namespace?"
```

---

## Installation

Requires Python 3.13+ and a reachable Kubernetes cluster.

```
git clone https://github.com/aahan-pat/graphnetes
cd graphnetes
uv sync
```

---

## Usage

**Build the graph from your current kubeconfig:**
```
uv run python -m graphnetes build
```

**Scope to a specific context or namespace:**
```
uv run python -m graphnetes build --context prod-us-east --namespace payments
```

**Exclude namespaces:**
```
uv run python -m graphnetes build --exclude-namespace kube-system --exclude-namespace monitoring
```

**All commands:**

| Command | Description |
|---|---|
| `build` | Connect to cluster, build graph, write output files |
| `path <source> <target>` | Shortest path between two resources |
| `inspect <node-id>` | Show full details and edges for a single node |
| `neighbors <node-id>` | Show direct neighbors of a node |
| `list <kind>` | List all nodes of a given kind |

All query commands (`path`, `inspect`, `neighbors`, `list`) read from `graphnetes-out/graph.json` by default. Use `--graph <path>` to point at a different file.

---

## Commands

### `build`

```
uv run python -m graphnetes build [OPTIONS]

Options:
  --kubeconfig PATH           Path to kubeconfig file
  --context, -c TEXT          Kubernetes context to use
  --namespace, -n TEXT        Scope to a single namespace
  --exclude-namespace, -e TEXT  Exclude a namespace (repeatable)
  --output, -o PATH           Output directory (default: graphnetes-out)
```

### `inspect <node-id>`

Show all fields, labels, metadata, and edges for a node. Node IDs use the form `Kind/namespace/name` for namespaced resources or `Kind/name` for cluster-scoped ones.

```
uv run python -m graphnetes inspect Service/prod/payments
uv run python -m graphnetes inspect Node/ip-10-0-1-5 --json
```

### `neighbors <node-id>`

Show the direct neighbors of a node, optionally filtered by edge direction.

```
uv run python -m graphnetes neighbors Deployment/prod/payments
uv run python -m graphnetes neighbors Deployment/prod/payments --direction out
```

`--direction` accepts `in`, `out`, or `both` (default).

### `path <source> <target>`

Find the shortest path between two nodes and print the edge relations along the way.

```
uv run python -m graphnetes path Ingress/prod/frontend Pod/prod/payments-6d4f9b
```

### `list <kind>`

List all nodes of a given kind, optionally filtered by namespace.

```
uv run python -m graphnetes list Pod --namespace prod
uv run python -m graphnetes list Service --json
```

---

## Output

Running `build` writes to `graphnetes-out/` by default:

```
graphnetes-out/
├── graph.json    # Persistent node-link JSON
└── graph.html    # Self-contained interactive visualization
```

`graph.html` opens directly in any browser — no server needed. Nodes are coloured by resource kind, edges show relation types, and clicking a node shows its full detail in the sidebar.

---

## How it works

```
[k8s API]
    │
 ingest/       connect to cluster, fetch raw resource dicts
    │
 extract/      parse dicts → ResourceNode + ResourceEdge
    │
 build/        construct NetworkX DiGraph + kind/namespace indexes
    │
 export/       write graph.json + graph.html
```

Each `ResourceNode` has an ID in the form `Kind/namespace/name` (or `Kind/name` for cluster-scoped resources). Each `ResourceEdge` carries a typed relation, a confidence level (`EXTRACTED` / `INFERRED` / `AMBIGUOUS`), and a weight.

### Supported resource kinds

| Category | Kinds |
|---|---|
| Workloads | Pod, Deployment, ReplicaSet, StatefulSet, DaemonSet |
| Networking | Service, Ingress, HorizontalPodAutoscaler |
| Config | ConfigMap, Secret, ServiceAccount |
| Storage | PersistentVolume, PersistentVolumeClaim |
| Infrastructure | Node, Namespace |

### Supported edge relations

| Relation | Example |
|---|---|
| `owns` | Deployment → ReplicaSet → Pod |
| `selects` | Deployment / Service → Pod |
| `routes_to` | Ingress → Service |
| `mounts` | Pod → ConfigMap / Secret / PVC |
| `uses_service_account` | Pod → ServiceAccount |
| `scheduled_on` | Pod → Node |
| `applies_to` | NetworkPolicy → Pod |
| `scales` | HPA → Deployment |
| `bound_to` | PVC → PV |
| `in_namespace` | any resource → Namespace |
| `grants` | RoleBinding → Role + ServiceAccount |
| `communicates_with` | inferred from NetworkPolicy allow rules |
| `configured_by` | resource → last-applied manifest snapshot |

---

## Configuration

Graphnetes resolves kubeconfig in this order:

1. `--kubeconfig <path>` flag
2. `KUBECONFIG` environment variable
3. `~/.kube/config`

---

## Dependencies

| Library | Role |
|---|---|
| `networkx` | Graph construction, traversal, shortest path |
| `kubernetes` | Official Python k8s API client |
| `typer` | CLI |
| `rich` | Terminal output |
