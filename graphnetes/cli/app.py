import typer

from .commands import build, path

app = typer.Typer(
    name="graphnetes",
    help="Knowledge graph engine for Kubernetes clusters.",
    no_args_is_help=True,
)

app.add_typer(build.app, name="build")
app.command("path", help="Find the shortest path between two resources.")(path.path_cmd)
