from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Start the MCP stdio server for agent integration.")
console = Console()


@app.callback(invoke_without_command=True)
def serve(
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
) -> None:
    console.print("[bold]Starting MCP server…[/bold]")
    console.print(f"Graph: {graph}")
    console.print("[yellow]Not implemented yet.[/yellow]")
