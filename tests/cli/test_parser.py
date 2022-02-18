from datetime import datetime
from typing import Type

import pytest

from elastic_log_cli.cli.parser import build_query, parse_specifier
from elastic_log_cli.exceptions import ElasticLogValidationError


class TestParseSpecifier:
    @staticmethod
    @pytest.mark.parametrize(
        "specifier,expected",
        [
            ("http", {"exists": {"field": "http"}}),
            ("environment=production", {"term": {"environment": {"value": "production"}}}),
            ("environment=produc\\~ion", {"term": {"environment": {"value": "produc~ion"}}}),
            ("http.status_code>499", {"range": {"http.status_code": {"gt": "499"}}}),
            ("@timestamp<2022-02-23T14:00:00", {"range": {"@timestamp": {"lt": "2022-02-23T14:00:00"}}}),
            ("message~error", {"match": {"message": {"query": "error"}}}),
            ("message~HTTP status *", {"match_phrase_prefix": {"message": {"query": "HTTP status "}}}),
            ("message=", ElasticLogValidationError),
            ("=", ElasticLogValidationError),
            ("message=message=message", ElasticLogValidationError),
        ]
    )
    def should_produce_expected_queries(specifier: str, expected: dict | Type[Exception]):
        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(expected):
                parse_specifier(specifier)
        else:
            assert parse_specifier(specifier) == expected


class TestBuildQuery:
    @staticmethod
    def should_produce_expected_queries_with_end_time():
        assert build_query(
            (
                "http",
                "environment=production",
                "http.duration>800",
            ),
            start=datetime.fromisoformat("2022-02-23T12:00:00"),
            end=datetime.fromisoformat("2022-02-23T14:00:00"),
            timestamp_field="time",
        ) == {
            "bool": {
                "must": [
                    {"range": {"time": {"gte": "2022-02-23T12:00:00", "lte": "2022-02-23T14:00:00"}}},
                    {"exists": {"field": "http"}},
                    {"term": {"environment": {"value": "production"}}},
                    {"range": {"http.duration": {"gt": "800"}}}
                ]
            }
        }

    @staticmethod
    def should_produce_expected_queries_without_end_time():
        assert build_query(
            (
                "http",
                "environment=production",
                "http.duration>800",
            ),
            start=datetime.fromisoformat("2022-02-23T12:00:00"),
            end=None,
            timestamp_field="time",
        ) == {
            "bool": {
                "must": [
                    {"range": {"time": {"gte": "2022-02-23T12:00:00"}}},
                    {"exists": {"field": "http"}},
                    {"term": {"environment": {"value": "production"}}},
                    {"range": {"http.duration": {"gt": "800"}}}
                ]
            }
        }
