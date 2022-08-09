import json
import sys
from datetime import datetime, timedelta

import click

from elastic_log_cli import __version__
from elastic_log_cli.config import get_settings
from elastic_log_cli.exceptions import ElasticLogError, ElasticLogValidationError
from elastic_log_cli.kql import parse
from elastic_log_cli.search import search_after_scan
from elastic_log_cli.utils.backoff import exponential_backoff


class CSV(click.ParamType):
    name = "csv"

    def convert(self, value, param, ctx) -> list[str]:
        if isinstance(value, list):
            return value
        return value.split(",")


@click.command()
@click.argument(
    "query",
    nargs=1,
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
    default=lambda: get_settings().elasticsearch_index,
    show_default="filebeat-*",
    help="The index to target. Globs are supported.",
)
@click.option(
    "--start",
    "-s",
    type=str,
    default=(datetime.now() - timedelta(hours=1)).isoformat(),
    help="When to begin streaming logs from.",
)
@click.option(
    "--end",
    "-e",
    type=str,
    default=None,
    help="When to stop streaming logs. Omit to continuously stream logs until interrupted.",
)
@click.option(
    "--source",
    type=CSV(),
    default=None,
    help="Source fields to retrieve, comma-separated. Default behaviour is to fetch full document.",
)
@click.option(
    "--timestamp-field",
    "-t",
    type=str,
    default=lambda: get_settings().elasticsearch_timestamp_field,
    show_default="@timestamp",
    help="The field which denotes the timestamp in the indexed logs.",
)
@click.option("--version", type=bool, default=False, is_flag=True, help="Show version and exit.")
def cli(
    query: str,
    *,
    page_size: int,
    index: str,
    start: str,
    end: str | None,
    source: list[str] | None,
    timestamp_field: str,
    version: bool,
):
    """Stream logs from Elasticsearch.

    Accepts a KQL query as its only positional argument.
    """
    if version:
        print(__version__)
        sys.exit(0)
    for doc in search_after_scan(
        index=index,
        query=query_from_args(query, start=start, end=end, timestamp_field=timestamp_field),
        sort=[{timestamp_field: {"order": "asc"}}, "_seq_no"],
        size=page_size,
        source=source,
        backoff=exponential_backoff(on_backoff=_log_backoff),
    ):
        print(json.dumps(doc["_source"], sort_keys=True))


def query_from_args(kql_query: str, *, start: str, end: str | None, timestamp_field: str) -> dict:
    time_filter = {"range": {timestamp_field: {"gte": start}}}
    if end:
        time_filter["range"][timestamp_field]["lte"] = end
    return {
        "bool": {
            "filter": [
                time_filter,
                parse(kql_query),
            ]
        }
    }


def _log_backoff(exception: Exception, amount: float) -> None:
    click.echo(f"Got error whilst querying Elasticsearch, backing off for {amount:.2f}s. Error: {exception}", err=True)


def run_cli():
    try:
        cli()
    except ElasticLogValidationError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(2)
    except ElasticLogError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)
