import json
from pathlib import Path

import typer
from rich.console import Console

from graphnetes.build.graph import GraphBuilder
from graphnetes.cli.commands._parse import suggest_nodes

console = Console()


def inspect_cmd(
    node_id: str = typer.Argument(..., help='Node ID to inspect, e.g. "Service/prod/payments".'),
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    if not graph.exists():
        console.print(f"[red]graph.json not found:[/red] {graph}. Run [bold]graphnetes build[/bold] first.")
        raise typer.Exit(code=1)

    builder = GraphBuilder.load(path=graph)
    node = builder.get_node_by_id(node_id)

    if node is None:
        console.print(f"[red]Error:[/red] node '{node_id}' not found.")
        suggestions = suggest_nodes(builder, node_id)
        if suggestions:
            console.print("\nDid you mean:")
            for suggestion in suggestions:
                console.print(f"  {suggestion}")
        else:
            console.print("Run [bold]graphnetes viz[/bold] to browse available nodes.")
        raise typer.Exit(code=1)

    outgoing = [
        {"relation": builder.graph.edges[node_id, t]["data"].relation.value, "target": t}
        for t in builder.graph.successors(node_id)
    ]
    incoming = [
        {"relation": builder.graph.edges[s, node_id]["data"].relation.value, "source": s}
        for s in builder.graph.predecessors(node_id)
    ]

    if as_json:
        output = {**node.to_dict(), "edges": {"outgoing": outgoing, "incoming": incoming}}
        console.print(json.dumps(output, indent=2))
        return

    color = "[bold cyan]"
    console.print(f"\n{color}[{node.kind.value}][/bold cyan] [bold]{node.name}[/bold]")
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
