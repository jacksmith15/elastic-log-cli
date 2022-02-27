from elastic_log_cli.kql.parser import get_parser, transform


class TestParseKQL:
    @staticmethod
    def should_produce_expected_tree_and_query():
        query = " foo:bar and not (qux>=mux or abc:def) and foo"
        parser = get_parser()  # To help distinguish grammar issues with parsing issues
        tree = parser.parse(query)
        result = transform(tree)
        assert result == {
            "query": [
                {
                    "bool": {
                        "filter": [
                            {"match": {"foo": "bar"}},
                            {
                                "bool": {
                                    "must_not": {
                                        "bool": {
                                            "should": [{"range": {"qux": {"gte": "mux"}}}, {"match": {"abc": "def"}}],
                                            "minimum_should_match": 1,
                                        }
                                    }
                                }
                            },
                            {"exists": {"field": "foo"}},
                        ]
                    }
                }
            ]
        }
