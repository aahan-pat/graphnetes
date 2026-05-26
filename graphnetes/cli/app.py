import typer

from .commands import build, inspect, list_nodes, neighbors, path

app = typer.Typer(
    name="graphnetes",
    help="Knowledge graph engine for Kubernetes clusters.",
    no_args_is_help=True,
)

app.add_typer(build.app, name="build")
app.command("path", help="Find the shortest path between two resources.")(path.path_cmd)
app.command("inspect", help="Show full details and edges for a single node.")(inspect.inspect_cmd)
app.command("neighbors", help="Show direct neighbors of a node.")(neighbors.neighbors_cmd)
app.command("list", help="List all nodes of a given kind.")(list_nodes.list_cmd)
