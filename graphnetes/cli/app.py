import typer

from .commands import anomalies, blast_radius, build, path, query, serve, viz

app = typer.Typer(
    name="graphnetes",
    help="Knowledge graph engine for Kubernetes clusters.",
    no_args_is_help=True,
)

app.add_typer(build.app, name="build")
app.add_typer(query.app, name="query")
app.command("path", help="Find the shortest path between two resources.")(path.path_cmd)
app.add_typer(blast_radius.app, name="blast-radius")
app.add_typer(anomalies.app, name="anomalies")
app.add_typer(serve.app, name="serve")
app.add_typer(viz.app, name="viz")
