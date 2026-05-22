from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Query the knowledge graph in natural language.")
console = Console()


@app.callback(invoke_without_command=True)
def query(
    question: str = typer.Argument(..., help='Natural language question, e.g. "what depends on redis?"'),
    mode: str = typer.Option("bfs", "--mode", "-m", help="Traversal mode: bfs or dfs."),
    depth: int = typer.Option(3, "--depth", "-d", help="Maximum traversal depth."),
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
) -> None:
    console.print(f"[bold]Query:[/bold] {question}")
    console.print(f"Mode: {mode}, depth: {depth}")
    console.print("[yellow]Not implemented yet.[/yellow]")
