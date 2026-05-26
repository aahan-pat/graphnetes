import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from graphnetes.build.graph import GraphBuilder
from graphnetes.cli.commands._parse import suggest_nodes

console = Console()


def neighbors_cmd(
    node_id: str = typer.Argument(..., help='Node ID to query, e.g. "Deployment/prod/payments".'),
    direction: str = typer.Option("both", "--direction", "-d", help="Edge direction: in, out, or both."),
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    if not graph.exists():
        console.print(f"[red]graph.json not found:[/red] {graph}. Run [bold]graphnetes build[/bold] first.")
        raise typer.Exit(code=1)

    if direction not in ("in", "out", "both"):
        console.print("[red]Error:[/red] --direction must be one of: in, out, both.")
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
    ] if direction in ("out", "both") else []

    incoming = [
        {"relation": builder.graph.edges[s, node_id]["data"].relation.value, "source": s}
        for s in builder.graph.predecessors(node_id)
    ] if direction in ("in", "both") else []

    if as_json:
        console.print(json.dumps({"outgoing": outgoing, "incoming": incoming}, indent=2))
        return

    console.print(f"\n[bold]Neighbors of[/bold] {node_id}\n")

    if outgoing:
        console.print(f"[dim]Outgoing ({len(outgoing)})[/dim]")
        for edge in outgoing:
            console.print(f"  [green]{edge['relation']}[/green] -> {edge['target']}")

    if incoming:
        console.print(f"\n[dim]Incoming ({len(incoming)})[/dim]")
        for edge in incoming:
            console.print(f"  [green]{edge['relation']}[/green] <- {edge['source']}")

    if not outgoing and not incoming:
        console.print("[dim]No neighbors found.[/dim]")
    console.print()
