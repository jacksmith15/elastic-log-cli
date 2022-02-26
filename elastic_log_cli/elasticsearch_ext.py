from collections.abc import Iterator
from typing import Union

from elasticsearch import ConnectionError as ElasticsearchConnectionError
from elasticsearch import Elasticsearch
from urllib3.exceptions import ReadTimeoutError

from elastic_log_cli.utils.backoff import Backoff, exponential_backoff


# TODO: error log on backoff

def search_after_scan(
    client: Elasticsearch,
    index: str,
    query: dict,
    sort: Union[list[Union[dict, str]], dict, str],
    source: list[str] = None,
    size: int = 1000,
    backoff: Backoff = None,
) -> Iterator[dict]:
    """Implementation of `search_after` pagination (without point-in-time).

    Will paginate through results and yield them. Back-off is performed on connection errors, by default using an
    exponential back-off of 2, 4, 8 ... seconds (up to 8.5 minutes).

    Notes:
        See https://www.elastic.co/guide/en/elasticsearch/reference/7.16/paginate-search-results.html#search-after
        Its poorly documented, but a sort _must_ be provided for `search_after` to work.

    Warning:
        This will only work if the search results do not change for the duration of the scan. A point-in-time search
        should instead be used for that case.
    """
    search_after = None
    backoff = backoff or exponential_backoff(base=2.0, factor=1.0, maximum=10)
    while True:
        with backoff.on(ElasticsearchConnectionError, ReadTimeoutError):
            result = client.search(
                index=index,
                query=query,
                _source=source,
                sort=sort,  # type: ignore[arg-type]
                size=size,
                search_after=search_after,
                track_total_hits=False,
            )
            hits = result["hits"]["hits"]
            if not hits:
                return
            search_after = hits[-1]["sort"]
            for hit in hits:
                yield hit
