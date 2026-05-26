from pathlib import Path

import typer
from rich.console import Console

from graphnetes.build.graph import GraphBuilder

console = Console()


def path_cmd(
    source: str = typer.Argument(..., help='Source node ID, e.g. "Deployment/prod/payments".'),
    target: str = typer.Argument(..., help='Target node ID, e.g. "Pod/prod/payments-6d4f9b".'),
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
) -> None:
    if not graph.exists():
        console.print(f"[red]graph.json not found:[/red] {graph}. Run [bold]graphnetes build[/bold] first.")
        raise typer.Exit(code=1)

    builder = GraphBuilder.load(path=graph)

    try:
        nodes = builder.shortest_path(source, target)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    for i, node in enumerate(nodes):
        console.print(f"[bold]{node.id}[/bold]", end="")
        if i < len(nodes) - 1:
            edge_data = builder.graph.edges[node.id, nodes[i + 1].id]["data"]
            console.print(f"  [dim]─{edge_data.relation.value}→[/dim] ", end="")
