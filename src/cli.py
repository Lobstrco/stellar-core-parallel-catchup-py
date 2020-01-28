import os

import click
import requests

from initialize import initialize_structure
from merge import merge_results
from monitor import monitor_workers


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(version="0.0.1")
def cli():
    pass


@cli.command(help="Initialize structure")
@click.option(
    "--start",
    default=1,
    help="First ledger to process (default 1)"
)
@click.option(
    "--end",
    default=None,
    help="Last ledger (default = last ledger available)"
)
@click.option(
    "--chunk",
    default=100000,
    help="Chunk size to process per job",
)
def initialize(start, end, chunk):
    if end is None:
        end = requests.get('https://horizon.stellar.org').json()['core_latest_ledger']
    initialize_structure(int(start), int(end), int(chunk))


@cli.command(help="Run monitor")
@click.option(
    "--workers",
    default=None,
    help="Workers number (default = cores number)"
)
def monitor(workers):
    if workers is None:
        workers = os.cpu_count()
    monitor_workers(workers)


@cli.command(help="Wait for results and merge them into the database")
def merge():
    merge_results()


if __name__ == "__main__":
    cli()
