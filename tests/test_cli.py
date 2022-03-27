from elastic_log_cli.cli import query_from_args


class TestQueryFromArgs:
    @staticmethod
    def should_produce_expected_query() -> None:
        assert query_from_args(
            kql_query="foo:bar and baz:*",
            start="2022-02-27T12:00:00",
            end="2022-02-27T13:00:00",
            timestamp_field="time",
        ) == {
            "bool": {
                "filter": [
                    {"range": {"time": {"gte": "2022-02-27T12:00:00", "lte": "2022-02-27T13:00:00"}}},
                    {"bool": {"filter": [{"match": {"foo": "bar"}}, {"exists": {"field": "baz"}}]}},
                ]
            }
        }
