import binascii
import os
from collections.abc import Iterator
from functools import cache
from urllib.parse import parse_qs, urlencode, urlparse

from requests import ConnectionError, PreparedRequest, Session, Timeout
from requests.auth import AuthBase

from elastic_log_cli import __version__
from elastic_log_cli.config import get_settings
from elastic_log_cli.utils.backoff import Backoff, exponential_backoff


class ElasticsearchError(Exception):
    pass


def search_after_scan(
    index: str,
    query: dict,
    sort: list[dict | str] | dict | str,
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
        with backoff.on(Timeout, ConnectionError):
            result = search(
                index=index,
                query=query,
                source=source,
                sort=sort,
                size=size,
                search_after=search_after,
            )
            hits = result["hits"]["hits"]
            if not hits:
                return
            search_after = hits[-1]["sort"]
            for hit in hits:
                yield hit


def search(
    index: str,
    query: dict,
    sort: list[dict | str] | dict | str,
    source: list[str] = None,
    size: int = 1000,
    search_after: list[str] = None,
) -> dict:
    client = get_client()

    body: dict = {
        "query": query,
        "sort": sort,
        "size": size,
    }
    if search_after:
        body["search_after"] = search_after
    if source:
        body["_source"] = source
    response = client.get(
        f"/{index}/_search",
        params={"track_total_hits": "false"},
        json=body,
    )
    try:
        response.raise_for_status()
    except Exception as exc:
        raise ElasticsearchError(response.status_code, response.text) from exc
    return response.json()


class SingleOriginSession(Session):
    """Requests session which targets a single origin, accepting only paths for each request."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        super().__init__()

    def request(
        self,
        method,
        url,
        params=None,
        data=None,
        headers=None,
        cookies=None,
        files=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        proxies=None,
        hooks=None,
        stream=None,
        verify=None,
        cert=None,
        json=None,
    ):
        url = self.base_url.rstrip("/") + "/" + url.lstrip("/")
        return super().request(
            method,
            url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            files=files,
            auth=auth,
            timeout=timeout,
            allow_redirects=allow_redirects,
            proxies=proxies,
            hooks=hooks,
            stream=stream,
            verify=verify,
            cert=cert,
            json=json,
        )


@cache
def get_client() -> SingleOriginSession:
    settings = get_settings()

    url = get_elasticsearch_url()
    session = SingleOriginSession(base_url=url)
    session.verify = True

    for key in set(session.headers):
        session.headers.pop(key)
    session.headers["accept-encoding"] = "gzip,deflate" if settings.is_cloud else None  # type: ignore
    session.headers["user-agent"] = f"elastic-log-cli-{__version__}"

    if settings.elasticsearch_auth_mode == "basicauth":
        user_pass = (settings.elasticsearch_username, settings.elasticsearch_password)
        if all(user_pass):
            session.auth = user_pass
    elif settings.elasticsearch_auth_mode == "apikey":
        api_key = (
            binascii.b2a_base64(f"{settings.elasticsearch_username}:{settings.elasticsearch_password}".encode("utf-8"))
            .rstrip(b"\r\n")
            .decode("utf-8")
        )
        session.headers["authorization"] = f"ApiKey {api_key}"
    elif settings.elasticsearch_auth_mode == "awssigv4":
        session.auth = get_awssigv4_auth()

    return session


@cache
def get_elasticsearch_url():
    settings = get_settings()
    if settings.is_cloud:
        port = 443
        _, cloud_id = settings.elasticsearch_url.removeprefix("cloud:").split(":")
        parent_domain_name, elasticsearch_uuid = (
            binascii.a2b_base64(cloud_id.encode("utf-8")).decode("utf-8").split("$")[:2]
        )
        if ":" in parent_domain_name:
            parent_domain_name, _, parent_port = parent_domain_name.split(":", 1)
            port = int(parent_port)
        return f"https://{elasticsearch_uuid}.{parent_domain_name}:{port}"
    return settings.elasticsearch_url


@cache
def get_awssigv4_auth():
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest

    from elastic_log_cli._compat import aws  # This will trigger errors if dependencies not installed

    class AWSV4SignerAuth(AuthBase):
        def __init__(self, credentials, region):
            if not credentials:
                raise ValueError("Credentials cannot be empty")
            self.credentials = credentials

            if not region:
                raise ValueError("Region cannot be empty")
            self.region = region

        def __call__(self, request: PreparedRequest) -> PreparedRequest:
            return self._sign_request(request)

        def _sign_request(self, prepared_request: PreparedRequest) -> PreparedRequest:

            url = self._parse_url(prepared_request)

            assert prepared_request.method
            aws_request = AWSRequest(
                method=prepared_request.method.upper(),
                url=url,
                data=prepared_request.body,
            )
            sig_v4_auth = SigV4Auth(self.credentials, "es", self.region)
            sig_v4_auth.add_auth(aws_request)

            prepared_request.headers.update(dict(aws_request.headers.items()))

            return prepared_request

        @staticmethod
        def _parse_url(prepared_request: PreparedRequest) -> str:
            url = urlparse(prepared_request.url)
            path = url.path or "/"

            querystring = ""
            if url.query:
                querystring = "?" + urlencode(parse_qs(url.query, keep_blank_values=True), doseq=True)

            headers = dict((key.lower(), value) for key, value in prepared_request.headers.items())
            location = headers.get("host") or url.netloc

            def _as_str(string: str | bytes) -> str:
                return string if isinstance(string, str) else string.decode("utf-8")

            parts = [
                url.scheme,
                "://",
                location,
                path,
                querystring,
            ]

            return "".join([_as_str(part) for part in parts])

    session = aws.boto3.Session(profile_name=os.getenv("AWS_PROFILE"))
    credentials = session.get_credentials()
    return AWSV4SignerAuth(credentials, session.region_name)
