import json
from pathlib import Path

from typer import Argument, Option
from rich.console import Console

from graphnetes.cli.commands._parse import collect_edges, load_graph, resolve_node
from graphnetes.models import ResourceNode

console = Console()


def _print_node(node: ResourceNode, outgoing: list, incoming: list) -> None:
    console.print(f"\n[bold cyan][{node.kind.value}][/bold cyan] [bold]{node.name}[/bold]")
    console.print(f"[dim]ID:[/dim]        {node.id}")
    console.print(f"[dim]Namespace:[/dim] {node.namespace or 'cluster-scoped'}")
    if node.labels:
        console.print("\n[dim]Labels[/dim]")
        for k, v in node.labels.items():
            console.print(f"  {k}: {v}")
    if node.metadata:
        console.print("\n[dim]Metadata[/dim]")
        for k, v in node.metadata.items():
            console.print(f"  {k}: {v}")
    if outgoing:
        console.print("\n[dim]Outgoing edges[/dim]")
        for edge in outgoing:
            console.print(f"  [green]{edge['relation']}[/green] → {edge['target']}")
    if incoming:
        console.print("\n[dim]Incoming edges[/dim]")
        for edge in incoming:
            console.print(f"  [green]{edge['relation']}[/green] ← {edge['source']}")
    console.print()


def inspect_cmd(
    node_id: str = Argument(..., help='Node ID to inspect, e.g. "Service/prod/payments".'),
    graph: Path = Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
    as_json: bool = Option(False, "--json", help="Output as JSON."),
) -> None:
    builder = load_graph(graph, console)
    node = resolve_node(builder, node_id, console)
    outgoing, incoming = collect_edges(builder, node_id)
    if as_json:
        output = {**node.to_dict(), "edges": {"outgoing": outgoing, "incoming": incoming}}
        console.print(json.dumps(output, indent=2))
        return
    _print_node(node, outgoing, incoming)
