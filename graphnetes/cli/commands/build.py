from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from graphnetes.build.graph import GraphBuilder
from graphnetes.export.graph import export
from graphnetes.extract import ExtractorRegistry
from graphnetes.ingest.static import StaticIngestor

app = typer.Typer(help="Build a knowledge graph from a live cluster or local manifests.")
console = Console()


@app.callback(invoke_without_command=True)
def build(
    kubeconfig: Optional[Path] = typer.Option(None, "--kubeconfig", help="Path to kubeconfig file."),
    context: Optional[str] = typer.Option(None, "--context", "-c", help="Kubernetes context to use."),
    namespace: Optional[str] = typer.Option(None, "--namespace", "-n", help="Scope to a single namespace."),
    output: Path = typer.Option(Path("graphnetes-out"), "--output", "-o", help="Output directory for graph files."),
) -> None:
    try:
        ingestor = StaticIngestor(
            kubeconfig=str(kubeconfig) if kubeconfig else None,
            context=context,
        )
    except (FileNotFoundError, RuntimeError) as error:
        console.print(f"[red]Failed to load kubeconfig:[/red] {error}")
        raise typer.Exit(code=1)

    console.print(f"[green]Connected to cluster:[/green] {ingestor.configuration.host}")

    builder = GraphBuilder()

    for raw in ingestor.fetch(namespace=namespace):
        extract = ExtractorRegistry.extractors.get(raw.get("kind", ""))
        if extract is None:
            continue
        nodes, edges = extract(raw)
        builder.add_nodes(nodes)
        builder.add_edges(edges)

    builder.build_selector_edges()

    stats = builder.stats()
    console.print(f"[green]Graph built:[/green] {stats['nodes']} nodes, {stats['edges']} edges")
    console.print(f"By kind: {stats['by_kind']}")

    export(builder, output)
    console.print(f"[green]Exported to[/green] {output}/")
