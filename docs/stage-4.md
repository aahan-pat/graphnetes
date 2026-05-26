# Stage 4: Analysis Layer and CLI Wiring

Stage 4 implements the `analyze/` module and wires it to the three deterministic CLI
commands: `blast-radius`, `path`, and `anomalies`. It also adds graph loading so those
commands can operate on a previously built `graph.json` without re-fetching the cluster.

Natural-language query (`graphnetes query`) and the MCP serve layer are deferred to
later stages — they require LLM integration and are independent of this stage.

---

## Part 1: Graph Loading

### Problem

`graph.json` is written by `export_json` as a `{"nodes": [...], "edges": [...]}` dict.
The three analysis commands all accept `--graph graph.json`, but there is currently no
way to reconstruct a `GraphBuilder` from that file. Without a loader, the commands cannot
call any analysis function.

### Solution: `GraphBuilder.load(path)`

Add a `load` classmethod to `GraphBuilder` that reads `graph.json` and returns a fully
populated builder — including the `_kind_index` and `_namespace_index` — so all existing
`get_node`, `get_nodes_by_kind`, and `get_namespace_subgraph` methods work on the loaded
graph.

```python
@classmethod
def load(cls, path: Path) -> GraphBuilder:
    """Reconstruct a GraphBuilder from a graph.json produced by export_json."""
```

**Node reconstruction:** Each node dict is turned back into a `ResourceNode` via
`ResourceNode.from_resource`. The `kind` field is a raw string in JSON; use
`ResourceKind.from_str` to convert it. Stub nodes (written by `_stub_node_from_id`)
have no `metadata` key; default to `{}`.

**Edge reconstruction:** Each edge dict has `source`, `target`, `relation`, `confidence`,
and `weight`. Convert `relation` via `EdgeRelation(d["relation"])` and `confidence` via
`Confidence(d["confidence"])`. Reconstruct as a `ResourceEdge` and call `add_edge`.

**Index integrity:** Use the existing `add_node` and `add_edge` methods so `_kind_index`
and `_namespace_index` are populated exactly as they are during a live build.

---

## Part 2: Node ID Arguments

### `path`

Source and target are passed as full node IDs — the same strings stored under `"id"` in
`graph.json` (e.g. `Deployment/prod/payments`, `Pod/payments/postgres-0`). No parsing
layer is needed; the strings are looked up directly in the graph.

```
graphnetes path Deployment/prod/payments Pod/payments/postgres-0
```

Cluster-scoped resources omit the namespace segment (`Node/ip-10-0-1-5`). Using full IDs
avoids cross-namespace ambiguity and lets users copy IDs directly from `graph.json` or
the HTML visualization.

### `blast-radius`

Takes a single resource in `kind/name` form with an optional `--namespace` flag. A parser
in `graphnetes/cli/commands/_parse.py` converts short aliases to the full node ID before
lookup.

| Alias | ResourceKind |
|---|---|
| `pod` | `POD` |
| `deploy`, `deployment` | `DEPLOYMENT` |
| `svc`, `service` | `SERVICE` |
| `rs`, `replicaset` | `REPLICA_SET` |
| `sts`, `statefulset` | `STATEFUL_SET` |
| `ds`, `daemonset` | `DAEMON_SET` |
| `cm`, `configmap` | `CONFIG_MAP` |
| `secret` | `SECRET` |
| `sa`, `serviceaccount` | `SERVICE_ACCOUNT` |
| `pv`, `persistentvolume` | `PERSISTENT_VOLUME` |
| `pvc`, `persistentvolumeclaim` | `PERSISTENT_VOLUME_CLAIM` |
| `ns`, `namespace` | `NAMESPACE` |
| `node` | `NODE` |
| `ing`, `ingress` | `INGRESS` |
| `hpa` | `HORIZONTAL_POD_AUTOSCALER` |

---

## Part 3: Fuzzy Node Suggestions

Node lookup is exact. If a user passes an ID that does not match any node in the graph,
all three commands should suggest the closest matches rather than printing a bare "not
found" error.

### Algorithm

Case-insensitive substring match against all node IDs in the graph. No external library
needed — `query.lower() in node_id.lower()` is sufficient for the common cases (wrong
case, partial name, truncated kind string).

```python
def suggest_nodes(builder: GraphBuilder, query: str, limit: int = 5) -> list[str]:
    """Return up to limit node IDs that contain query as a case-insensitive substring."""
```

Located in `graphnetes/cli/commands/_parse.py`.

### Error message format

```
Error: node 'deployment/prod/payments' not found.

Did you mean:
  Deployment/prod/payments
  Deployment/prod/payments-worker
```

The suggestions are printed to stderr before exiting with code 1. If no suggestions are
found, the error message is:

```
Error: node 'xyz' not found. Run 'graphnetes viz' to browse available nodes.
```

---

## Part 3: `analyze/` Module

New package at `graphnetes/analyze/`. Four public functions, all operating on a
`GraphBuilder`.

### `blast_radius`

```python
def blast_radius(
    builder: GraphBuilder,
    source_id: str,
    depth: int = 5,
) -> list[tuple[ResourceNode, ResourceEdge]]:
```

Reverse BFS from `source_id`. Returns every node that has a directed path *to* the
source — i.e., every resource that depends on it transitively. Each entry is paired
with the edge that connects it to its predecessor in the BFS tree, so callers know
*why* each resource is affected.

Uses `nx.bfs_successors(builder.graph.reverse(copy=False), source_id, depth_limit=depth)`.

**Example:** deleting a ConfigMap → Pods that mount it → ReplicaSets that own those
Pods → Services that select those Pods → Ingresses that route to those Services.

### `dependency_tree`

```python
def dependency_tree(
    builder: GraphBuilder,
    source_id: str,
    depth: int = 5,
) -> list[tuple[ResourceNode, ResourceEdge]]:
```

Forward BFS from `source_id`. Returns every resource that `source_id` depends on
transitively. Uses `nx.bfs_successors(builder.graph, source_id, depth_limit=depth)`.

**Example:** a Deployment → ReplicaSet → Pods → Node, ServiceAccount, ConfigMaps, Secrets.

### `shortest_path`

```python
def shortest_path(
    builder: GraphBuilder,
    source_id: str,
    target_id: str,
) -> list[ResourceNode]:
```

Returns the list of `ResourceNode` objects on the shortest directed path from source to
target. Raises `ValueError` if no path exists or either node is not in the graph.

Uses `nx.shortest_path(builder.graph, source=source_id, target=target_id)`.

Stub nodes (no `data` attribute) encountered on the path are represented as a minimal
`ResourceNode` reconstructed from the node ID.

### `anomalies`

```python
def anomalies(builder: GraphBuilder) -> list[Anomaly]:
```

Scans the graph for structural issues. Returns a list of `Anomaly` named tuples:
`(kind, name, namespace, issue)`.

| Check | Condition | Issue label |
|---|---|---|
| Orphaned Pod | Pod node with no incoming `owns` edge | `no_owner` |
| Empty Service | Service node with no outgoing `selects` edges | `no_backends` |
| Unbound PVC | PVC node with no outgoing `bound_to` edge | `unbound` |
| Stale ReplicaSet | ReplicaSet node with `metadata["replicas"] == 0` | `zero_replicas` |
| Broken Ingress route | Ingress has `routes_to` edge to a stub Service (no `data` attribute) | `missing_service` |

The `Anomaly` type is a `NamedTuple` defined in `analyze/__init__.py`:

```python
class Anomaly(NamedTuple):
    kind: str
    name: str
    namespace: str | None
    issue: str
```

---

## Part 4: CLI Wiring

Each command loads graph.json, parses resource arguments, calls the analyze function,
and renders output with `rich`.

### `blast-radius`

```
graphnetes blast-radius deploy/payments --namespace prod --depth 5
```

Output: a `rich.tree.Tree` rooted at the source resource. Each branch is one hop in the
reverse BFS; nodes are colored by kind; the edge relation is shown as a dim label between
parent and child.

### `path`

```
graphnetes path ing/frontend pod/postgres-0 --namespace prod
```

Output: a vertical list of nodes with edge relations between each hop, e.g.:

```
Ingress/frontend
  --[routes_to]--> Service/backend
  --[selects]-->   Pod/backend-6d4f9b
```

If no path exists, print a clear error and exit with code 1.

### `anomalies`

```
graphnetes anomalies --graph graphnetes-out/graph.json
```

Output: a `rich.table.Table` with columns Kind, Name, Namespace, and Issue. Grouped by
issue type. Prints "No anomalies found." if the table is empty.

---

## File Layout

```
graphnetes/
├── analyze/
│   ├── __init__.py          # Anomaly NamedTuple; re-exports public functions
│   ├── traversal.py         # blast_radius, dependency_tree, shortest_path
│   └── checks.py            # anomalies()
├── build/
│   └── graph.py             # + GraphBuilder.load() classmethod
└── cli/
    └── commands/
        ├── _parse.py        # parse_resource_arg() for blast-radius; suggest_nodes() for all three
        ├── blast_radius.py  # wired
        ├── path.py          # wired
        └── anomalies.py     # wired
```

---

## Implementation Order

1. Add `GraphBuilder.load(path)` to `build/graph.py`.
2. Add `_parse.py` with `parse_resource_arg` and `suggest_nodes`.
3. Implement `analyze/traversal.py` (`blast_radius`, `dependency_tree`, `shortest_path`).
4. Implement `analyze/checks.py` (`anomalies`).
5. Wire `blast_radius.py`, `path.py`, `anomalies.py` CLI commands.

---

## Limitations

- `blast_radius` and `dependency_tree` return nodes in BFS order, not ranked by blast
  severity. Severity ranking is a future enhancement.
- `shortest_path` follows directed edges only. If no directed path exists between two
  nodes that are connected via undirected traversal, the command reports no path — it
  does not fall back to undirected search.
- The `anomalies` checks are structural only. They do not inspect resource status fields
  (e.g., a Pod that is CrashLooping but has an owner is not flagged). Runtime health
  checks are out of scope.
- `query` (natural-language traversal) is not part of this stage.
