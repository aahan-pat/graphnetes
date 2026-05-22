from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Detect graph-level anomalies in the cluster.")
console = Console()


@app.callback(invoke_without_command=True)
def anomalies(
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
) -> None:
    console.print("[bold]Scanning for anomalies…[/bold]")
    console.print("Checks: orphaned Services, Pods without selectors, unbound PVCs, stale ReplicaSets")
    console.print("[yellow]Not implemented yet.[/yellow]")
