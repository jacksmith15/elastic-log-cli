import sys
import json
from datetime import datetime, timedelta

import click

from elastic_log_cli import __version__
from elastic_log_cli.client import elasticsearch_client
from elastic_log_cli.cli.parser import build_query
from elastic_log_cli.elasticsearch_ext import search_after_scan
from elastic_log_cli.exceptions import ElasticLogError, ElasticLogValidationError


@click.command()
@click.argument(
    "specifiers",
    nargs=-1,
)
@click.option(
    "--page-size",
    "-p",
    type=click.IntRange(min=0),
    default=2000,
    help="The number of logs to fetch per page",
)
@click.option(
    "--index",
    "-i",
    type=str,
    default="filebeat-*",
    help="The index to target. Globs are supported."
)
@click.option(
    "--start",
    "-s",
    type=click.DateTime(),
    default=datetime.now() - timedelta(hours=1),
    help="When to begin streaming logs from.",
)
@click.option(
    "--end",
    "-e",
    type=click.DateTime(),
    default=None,
    help="When to stop streaming logs. Omit to continuously stream logs until interrupted.",
)
@click.option(
    "--timestamp-field",
    "-t",
    type=str,
    default="@timestamp",
    help="The field which denotes the timestamp in the indexed logs."
)
@click.option("--version", type=bool, default=False, is_flag=True, help="Show version and exit.")
def cli(specifiers: tuple[str, ...], *, page_size: int, index: str, start: datetime, end: datetime | None, timestamp_field: str, version: bool):
    """Stream logs from Elastic."""
    if version:
        print(__version__)
        sys.exit(0)
    query = build_query(
        specifiers,
        start=start,
        end=end,
        timestamp_field=timestamp_field,
    )
    client = elasticsearch_client()
    for doc in search_after_scan(
        client,
        index=index,
        query=query,
        sort=[{timestamp_field: {"order": "asc"}}, "_seq_no"],
        size=page_size,
    ):
        print(json.dumps(doc["_source"], sort_keys=True))


def run_cli():
    try:
        cli()
    except ElasticLogValidationError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(2)
    except ElasticLogError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)
