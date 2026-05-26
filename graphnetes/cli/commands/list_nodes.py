import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from graphnetes.build.graph import GraphBuilder
from graphnetes.models import ResourceKind

console = Console()


def list_cmd(
    kind: str = typer.Argument(..., help='Resource kind to list, e.g. "Pod", "Service".'),
    namespace: Optional[str] = typer.Option(None, "--namespace", "-n", help="Filter by namespace."),
    graph: Path = typer.Option(Path("graphnetes-out/graph.json"), "--graph", "-g", help="Path to graph.json."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    if not graph.exists():
        console.print(f"[red]graph.json not found:[/red] {graph}. Run [bold]graphnetes build[/bold] first.")
        raise typer.Exit(code=1)

    resource_kind = ResourceKind.from_str(kind)
    if resource_kind == ResourceKind.UNKNOWN:
        console.print(f"[red]Error:[/red] unknown kind '{kind}'.")
        raise typer.Exit(code=1)

    builder = GraphBuilder.load(path=graph)
    nodes = builder.get_nodes_by_kind(resource_kind)

    if namespace:
        nodes = [n for n in nodes if n.namespace == namespace]

    if as_json:
        console.print(json.dumps([n.to_dict() for n in nodes], indent=2))
        return

    label = f"{kind}s" if not kind.endswith("s") else kind
    ns_label = f" in [bold]{namespace}[/bold]" if namespace else ""
    console.print(f"\n[bold]{label}[/bold]{ns_label} ({len(nodes)})\n")

    for node in sorted(nodes, key=lambda n: n.id):
        console.print(f"  {node.id}")
    console.print()
