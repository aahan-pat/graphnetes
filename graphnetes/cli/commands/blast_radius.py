from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(help="Show everything that would break if a resource were deleted.")
console = Console()


@app.callback(invoke_without_command=True)
def blast_radius(
    resource: str = typer.Argument(..., help='Resource to analyse, e.g. "deploy/payments".'),
    namespace: Optional[str] = typer.Option(None, "--namespace", "-n", help="Namespace of the resource."),
    depth: int = typer.Option(5, "--depth", "-d", help="Maximum reverse-traversal depth."),
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
) -> None:
    console.print(f"[bold]Blast radius:[/bold] {resource}")
    console.print("[yellow]Not implemented yet.[/yellow]")
