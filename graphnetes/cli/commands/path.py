from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Find the shortest path between two resources.")
console = Console()


@app.callback(invoke_without_command=True)
def path(
    source: str = typer.Argument(..., help='Source resource, e.g. "deploy/frontend".'),
    target: str = typer.Argument(..., help='Target resource, e.g. "svc/backend".'),
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
) -> None:
    console.print(f"[bold]Path:[/bold] {source} -> {target}")
    console.print("[yellow]Not implemented yet.[/yellow]")
