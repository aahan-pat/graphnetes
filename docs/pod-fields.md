# Pod Fields

Fields extracted from the kubernetes API `V1Pod` object and their relevance to Graphnetes.

---

## Keep — used to build nodes and edges

| Field | Why |
|---|---|
| `metadata.name` | Pod name — part of the node ID |
| `metadata.namespace` | Namespace — part of the node ID, `in_namespace` edge |
| `metadata.uid` | Stable identity across renames |
| `metadata.labels` | Used by Services/Deployments to select this pod |
| `metadata.owner_references` | `owns` edge — points to the ReplicaSet/Job that controls this pod |
| `spec.node_name` | `scheduled_on` edge → Node |
| `spec.service_account_name` | `uses_service_account` edge → ServiceAccount |
| `spec.volumes` | `mounts` edges — each volume entry that has `config_map`, `secret`, or `persistent_volume_claim` set |
| `spec.containers[].name` | Container node identity |
| `spec.containers[].image` | Container metadata |
| `spec.containers[].volume_mounts` | Which volumes each container actually mounts |

## Keep — useful for anomaly detection

| Field | Why |
|---|---|
| `status.phase` | Running / Pending / Failed — spot unhealthy pods |
| `status.conditions` | Ready, PodScheduled — detect pods stuck in unscheduled state |

## Discard

- `managed_fields` — internal k8s bookkeeping, very verbose, zero graph value
- `metadata.resource_version`, `self_link`, `generation` — k8s internal versioning
- `api_version: null` / `kind: null` — come back null from list endpoints; hardcode `"Pod"` from context instead
- `spec.security_context`, probes, `tolerations`, `affinity`, `priority` — runtime scheduling config, not graph relationships
- All null volume types (`aws_elastic_block_store`, `azure_disk`, etc.) — only the non-null volume type matters per volume entry
