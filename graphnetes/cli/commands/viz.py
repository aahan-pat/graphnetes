import webbrowser
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Open the interactive graph visualisation in a browser.")
console = Console()


@app.callback(invoke_without_command=True)
def viz(
    graph_html: Path = typer.Option(Path("graphnetes-out/graph.html"), "--file", "-f", help="Path to graph.html."),
) -> None:
    if not graph_html.exists():
        console.print(f"[red]graph.html not found at {graph_html}. Run `graphnetes build` first.[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold]Opening[/bold] {graph_html}")
    webbrowser.open(graph_html.resolve().as_uri())
