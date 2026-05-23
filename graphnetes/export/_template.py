HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Graphnetes</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      display: flex;
      height: 100vh;
      overflow: hidden;
    }

    #graph {
      flex: 1;
      height: 100vh;
    }

    #sidebar {
      width: 320px;
      background: #1a1d27;
      border-left: 1px solid #2d3148;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    #sidebar-header {
      padding: 16px;
      border-bottom: 1px solid #2d3148;
    }

    #sidebar-header h1 {
      font-size: 16px;
      font-weight: 600;
      color: #a78bfa;
      letter-spacing: 0.05em;
    }

    #sidebar-header p {
      font-size: 12px;
      color: #64748b;
      margin-top: 4px;
    }

    #filters {
      padding: 12px 16px;
      border-bottom: 1px solid #2d3148;
    }

    #filters label {
      font-size: 11px;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      display: block;
      margin-bottom: 6px;
    }

    #namespace-filter {
      width: 100%;
      background: #0f1117;
      border: 1px solid #2d3148;
      color: #e2e8f0;
      padding: 6px 8px;
      border-radius: 4px;
      font-size: 13px;
    }

    #detail {
      flex: 1;
      padding: 16px;
      overflow-y: auto;
    }

    #detail-placeholder {
      color: #475569;
      font-size: 13px;
    }

    .detail-kind {
      display: inline-block;
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 3px;
      margin-bottom: 10px;
      letter-spacing: 0.05em;
    }

    .detail-name {
      font-size: 15px;
      font-weight: 600;
      margin-bottom: 4px;
      word-break: break-all;
    }

    .detail-namespace {
      font-size: 12px;
      color: #64748b;
      margin-bottom: 16px;
    }

    .detail-section {
      margin-top: 14px;
    }

    .detail-section-title {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #64748b;
      margin-bottom: 6px;
    }

    .detail-row {
      font-size: 12px;
      color: #94a3b8;
      padding: 4px 0;
      border-bottom: 1px solid #1e2235;
      display: flex;
      justify-content: space-between;
      gap: 8px;
    }

    .detail-row span:last-child {
      color: #e2e8f0;
      text-align: right;
      word-break: break-all;
    }

    #legend {
      padding: 12px 16px;
      border-top: 1px solid #2d3148;
    }

    #legend label {
      font-size: 11px;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      display: block;
      margin-bottom: 8px;
    }

    .legend-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4px;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      color: #94a3b8;
    }

    .legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }
  </style>
</head>
<body>

<div id="graph"></div>

<div id="sidebar">
  <div id="sidebar-header">
    <h1>GRAPHNETES</h1>
    <p id="graph-stats"></p>
  </div>

  <div id="filters">
    <label>Namespace</label>
    <select id="namespace-filter">
      <option value="">All namespaces</option>
    </select>
  </div>

  <div id="detail">
    <p id="detail-placeholder">Click a node to inspect it.</p>
  </div>

  <div id="legend">
    <label>Node kinds</label>
    <div class="legend-grid" id="legend-grid"></div>
  </div>
</div>

<script>
const RAW = __GRAPH_DATA__;

const KIND_COLORS = {
  Pod:                      "#6366f1",
  Deployment:               "#8b5cf6",
  ReplicaSet:               "#a78bfa",
  StatefulSet:              "#7c3aed",
  DaemonSet:                "#5b21b6",
  Job:                      "#c4b5fd",
  CronJob:                  "#ddd6fe",
  Service:                  "#22d3ee",
  Ingress:                  "#06b6d4",
  NetworkPolicy:            "#0891b2",
  EndpointSlice:            "#67e8f9",
  ConfigMap:                "#fbbf24",
  Secret:                   "#f59e0b",
  PersistentVolume:         "#34d399",
  PersistentVolumeClaim:    "#10b981",
  StorageClass:             "#059669",
  ServiceAccount:           "#f472b6",
  Role:                     "#ec4899",
  ClusterRole:              "#db2777",
  RoleBinding:              "#f9a8d4",
  ClusterRoleBinding:       "#fbcfe8",
  Node:                     "#94a3b8",
  Namespace:                "#64748b",
  Cluster:                  "#475569",
  HorizontalPodAutoscaler:  "#fb923c",
  VerticalPodAutoscaler:    "#f97316",
  PodDisruptionBudget:      "#ea580c",
  Unknown:                  "#334155",
};

function colorFor(kind) {
  return KIND_COLORS[kind] || "#334155";
}

// Populate namespace filter
const namespaces = [...new Set(
  RAW.nodes.map(n => n.namespace).filter(Boolean)
)].sort();
const select = document.getElementById("namespace-filter");
namespaces.forEach(ns => {
  const opt = document.createElement("option");
  opt.value = ns;
  opt.textContent = ns;
  select.appendChild(opt);
});

// Build legend
const legendGrid = document.getElementById("legend-grid");
const kindsInGraph = [...new Set(RAW.nodes.map(n => n.kind))].sort();
kindsInGraph.forEach(kind => {
  const item = document.createElement("div");
  item.className = "legend-item";
  item.innerHTML = `<div class="legend-dot" style="background:${colorFor(kind)}"></div><span>${kind}</span>`;
  legendGrid.appendChild(item);
});

// Stats
document.getElementById("graph-stats").textContent =
  `${RAW.nodes.length} nodes · ${RAW.edges.length} edges`;

function buildDatasets(namespaceFilter) {
  const visibleNodeIds = new Set(
    RAW.nodes
      .filter(n => !namespaceFilter || n.namespace === namespaceFilter)
      .map(n => n.id)
  );

  const nodes = RAW.nodes
    .filter(n => visibleNodeIds.has(n.id))
    .map(n => ({
      id: n.id,
      label: n.name,
      title: n.id,
      color: {
        background: colorFor(n.kind),
        border: colorFor(n.kind),
        highlight: { background: "#fff", border: colorFor(n.kind) },
      },
      font: { color: "#fff", size: 11 },
      shape: "dot",
      size: 14,
      _raw: n,
    }));

  const edges = RAW.edges
    .filter(e => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target))
    .map((e, i) => ({
      id: i,
      from: e.source,
      to: e.target,
      label: e.relation,
      font: { color: "#ffffff", size: 9, align: "middle", strokeWidth: 0 },
      color: { color: "#2d3148", highlight: "#6366f1" },
      arrows: { to: { enabled: true, scaleFactor: 0.6 } },
      smooth: { type: "curvedCW", roundness: 0.1 },
      _raw: e,
    }));

  return { nodes, edges };
}

let network;

function render(namespaceFilter) {
  const { nodes, edges } = buildDatasets(namespaceFilter);

  const container = document.getElementById("graph");
  const data = {
    nodes: new vis.DataSet(nodes),
    edges: new vis.DataSet(edges),
  };

  const options = {
    physics: {
      solver: "forceAtlas2Based",
      forceAtlas2Based: { gravitationalConstant: -60, springLength: 120 },
      stabilization: { iterations: 150 },
    },
    interaction: { hover: true, tooltipDelay: 100 },
  };

  if (network) network.destroy();
  network = new vis.Network(container, data, options);

  network.on("click", params => {
    if (!params.nodes.length) return;
    const nodeId = params.nodes[0];
    const node = nodes.find(n => n.id === nodeId);
    if (node) showDetail(node._raw, edges, nodeId);
  });
}

function showDetail(node, edges, nodeId) {
  const color = colorFor(node.kind);
  const incoming = edges.filter(e => e.to === nodeId);
  const outgoing = edges.filter(e => e.from === nodeId);

  let html = `
    <div class="detail-kind" style="background:${color}22;color:${color}">${node.kind}</div>
    <div class="detail-name">${node.name}</div>
    <div class="detail-namespace">${node.namespace || "cluster-scoped"}</div>
  `;

  if (Object.keys(node.labels || {}).length) {
    html += `<div class="detail-section">
      <div class="detail-section-title">Labels</div>`;
    for (const [k, v] of Object.entries(node.labels)) {
      html += `<div class="detail-row"><span>${k}</span><span>${v}</span></div>`;
    }
    html += `</div>`;
  }

  if (outgoing.length) {
    html += `<div class="detail-section">
      <div class="detail-section-title">Outgoing edges</div>`;
    outgoing.forEach(e => {
      html += `<div class="detail-row"><span>${e._raw.relation}</span><span>${e._raw.target}</span></div>`;
    });
    html += `</div>`;
  }

  if (incoming.length) {
    html += `<div class="detail-section">
      <div class="detail-section-title">Incoming edges</div>`;
    incoming.forEach(e => {
      html += `<div class="detail-row"><span>${e._raw.relation}</span><span>${e._raw.source}</span></div>`;
    });
    html += `</div>`;
  }

  document.getElementById("detail").innerHTML = html;
}

select.addEventListener("change", () => render(select.value));
render("");
</script>
</body>
</html>"""
