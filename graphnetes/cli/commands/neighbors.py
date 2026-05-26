import json
from pathlib import Path

import typer
from rich.console import Console

from graphnetes.cli.commands._parse import collect_edges, load_graph, resolve_node

console = Console()


def neighbors_cmd(
    node_id: str = typer.Argument(..., help='Node ID to query, e.g. "Deployment/prod/payments".'),
    direction: str = typer.Option("both", "--direction", "-d", help="Edge direction: in, out, or both."),
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    if direction not in ("in", "out", "both"):
        console.print("[red]Error:[/red] --direction must be one of: in, out, both.")
        raise typer.Exit(code=1)

    builder = load_graph(graph, console)
    resolve_node(builder, node_id, console)
    outgoing, incoming = collect_edges(builder, node_id, direction)

    if as_json:
        console.print(json.dumps({"outgoing": outgoing, "incoming": incoming}, indent=2))
        return

    console.print(f"\n[bold]Neighbors of[/bold] {node_id}\n")

    if outgoing:
        console.print(f"[dim]Outgoing ({len(outgoing)})[/dim]")
        for edge in outgoing:
            console.print(f"  [green]{edge['relation']}[/green] → {edge['target']}")

    if incoming:
        console.print(f"\n[dim]Incoming ({len(incoming)})[/dim]")
        for edge in incoming:
            console.print(f"  [green]{edge['relation']}[/green] ← {edge['source']}")

    if not outgoing and not incoming:
        console.print("[dim]No neighbors found.[/dim]")
    console.print()
