# Graphnetes

A knowledge graph engine for Kubernetes clusters. Every resource becomes a node, every relationship becomes a typed edge — giving you a queryable graph that answers questions `kubectl` cannot.

```
graphnetes build --context prod --namespace payments
graphnetes viz
```

---

## What it does

Graphnetes connects to a live cluster, snapshots all resources, and builds a directed graph of how they relate to each other. You can then query that graph to understand dependencies, trace paths, find blast radii, and detect anomalies — from the CLI or from an AI agent via MCP.

```
"What breaks if I delete the redis Deployment?"
"Which ServiceAccounts have cluster-admin privileges?"
"Trace the path from the frontend Ingress to the database Pod."
"Are there any Services with no pods behind them?"
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
uv run python main.py build
```

**Scope to a specific context or namespace:**
```
uv run python main.py build --context prod-us-east --namespace payments
```

**Open the browser visualization:**
```
uv run python main.py viz
```

**All commands:**

| Command | Description |
|---|---|
| `build` | Connect to cluster, build graph, write output files |
| `query "<question>"` | Natural-language query over the graph |
| `path <source> <target>` | Shortest path between two resources |
| `blast-radius <resource>` | Everything that breaks if this resource is deleted |
| `anomalies` | Scan for orphaned services, unbound PVCs, etc. |
| `serve` | Start the MCP stdio server for agent integration |
| `viz` | Open `graph.html` in a browser |

---

## Output

Running `build` writes to `graphnetes-out/` by default (`--output` to override):

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
 build/        construct NetworkX DiGraph + O(1) kind/namespace indexes
    │
 export/       write graph.json + graph.html
```

Each `ResourceNode` has an ID in the form `Kind/namespace/name` (or `Kind/name` for cluster-scoped resources). Each `ResourceEdge` carries a typed relation, a confidence level (`EXTRACTED` / `INFERRED` / `AMBIGUOUS`), and a weight.

**Supported edge relations:**

| Relation | Example |
|---|---|
| `owns` | ReplicaSet → Pod |
| `selects` | Service → Pod |
| `routes_to` | Ingress → Service |
| `mounts` | Pod → ConfigMap / Secret / PVC |
| `uses_service_account` | Pod → ServiceAccount |
| `scheduled_on` | Pod → Node |
| `applies_to` | NetworkPolicy → Pod |
| `scales` | HPA → Deployment |
| `bound_to` | PVC → PV |
| `in_namespace` | any resource → Namespace |
| `grants` | RoleBinding → Role + ServiceAccount |

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

---

## Status

Early development. The full ingest → extract → build → export pipeline is working for Pod resources. Remaining resource kinds, the `analyze/` traversal layer, natural-language query, and the MCP server are in progress.
