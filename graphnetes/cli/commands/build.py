from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(help="Build a knowledge graph from a live cluster or local manifests.")
console = Console()


@app.callback(invoke_without_command=True)
def build(
    kubeconfig: Optional[Path] = typer.Option(None, "--kubeconfig", help="Path to kubeconfig file."),
    context: Optional[str] = typer.Option(None, "--context", "-c", help="Kubernetes context to use."),
    namespace: Optional[str] = typer.Option(None, "--namespace", "-n", help="Scope to a single namespace."),
    from_file: Optional[Path] = typer.Option(None, "--from-file", "-f", help="Build from a YAML file or directory."),
    output: Path = typer.Option(Path("graphnetes-out"), "--output", "-o", help="Output directory for graph files."),
) -> None:
    if from_file:
        console.print(f"[bold]Building graph from[/bold] {from_file}")
    else:
        ctx = context or "current context"
        ns = namespace or "all namespaces"
        console.print(f"[bold]Building graph[/bold] — context: {ctx}, namespace: {ns}")

    console.print("[yellow]Not implemented yet.[/yellow]")
