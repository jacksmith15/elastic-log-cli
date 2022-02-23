from functools import cache

from elasticsearch import Elasticsearch

from elastic_log_cli.config import get_settings


@cache
def elasticsearch_client() -> Elasticsearch:
    """Retrieve cached elasticsearch client.

    Reads configuration dynamically from the environment, supporting
    - HTTP or API Key auth
    - Either a cloud ID or an Elasticsearch URL
    """
    settings = get_settings()
    options = {"timeout": settings.elasticsearch_timeout}
    auth: dict = {}
    if settings.elasticsearch_username and settings.elasticsearch_password:
        auth_value = (settings.elasticsearch_username, settings.elasticsearch_password)
        if settings.elasticsearch_auth_mode == "basicauth":
            auth = {"http_auth": auth_value}
        else:
            auth = {"api_key": auth_value}
    if settings.elasticsearch_url.startswith("cloud:"):
        return Elasticsearch(
            cloud_id=settings.elasticsearch_url.removeprefix("cloud:"),
            **auth,
            **options,
        )
    return Elasticsearch(
        [settings.elasticsearch_url],
        **auth,
        **options,
    )
