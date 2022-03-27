import pytest

from elastic_log_cli.kql.parser import get_parser, parse, transform


class TestParseKQL:
    @staticmethod
    def should_produce_expected_tree_and_query():
        query = " foo:bar and not (qux>=mux or abc:def) and foo"
        parser = get_parser()  # To help distinguish grammar issues with parsing issues
        tree = parser.parse(query)
        result = transform(tree)
        assert result == {
            "bool": {
                "filter": [
                    {"match": {"foo": "bar"}},
                    {
                        "bool": {
                            "must_not": [
                                {
                                    "bool": {
                                        "should": [{"range": {"qux": {"gte": "mux"}}}, {"match": {"abc": "def"}}],
                                        "minimum_should_match": 1,
                                    }
                                }
                            ]
                        }
                    },
                    {"exists": {"field": "foo"}},
                ]
            }
        }

    @staticmethod
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("foo", {"exists": {"field": "foo"}}),
            ("foo:*", {"exists": {"field": "foo"}}),
            ("foo:bar", {"match": {"foo": "bar"}}),
            ("foo>bar", {"range": {"foo": {"gt": "bar"}}}),
            ("foo>=bar", {"range": {"foo": {"gte": "bar"}}}),
            ("foo<bar", {"range": {"foo": {"lt": "bar"}}}),
            ("foo<=bar", {"range": {"foo": {"lte": "bar"}}}),
            ('"foo"', {"exists": {"field": "foo"}}),
            ('"foo":"*"', {"exists": {"field": "foo"}}),
            ('"foo":"bar"', {"match": {"foo": "bar"}}),
            ('"foo">"bar"', {"range": {"foo": {"gt": "bar"}}}),
            ('"foo">="bar"', {"range": {"foo": {"gte": "bar"}}}),
            ('"foo"<"bar"', {"range": {"foo": {"lt": "bar"}}}),
            ('"foo"<="bar"', {"range": {"foo": {"lte": "bar"}}}),
            ('foo:"bar\\"baz"', {"match": {"foo": 'bar"baz'}}),
            ("foo:bar baz", {"match": {"foo": "bar baz"}}),
            (r"foo:bar\:baz", {"match": {"foo": "bar:baz"}}),
            (r"foo:bar\u005dbaz", {"match": {"foo": "bar]baz"}}),
            (r"foo:bar \and baz", {"match": {"foo": "bar and baz"}}),
            (r"foo:bar\tbaz", {"match": {"foo": "bar\tbaz"}}),
            (" foo ", {"exists": {"field": "foo"}}),
            ("foo:bar and qux:mux", {"bool": {"filter": [{"match": {"foo": "bar"}}, {"match": {"qux": "mux"}}]}}),
            (
                "foo:bar or qux:mux",
                {"bool": {"minimum_should_match": 1, "should": [{"match": {"foo": "bar"}}, {"match": {"qux": "mux"}}]}},
            ),
            ("not foo:bar", {"bool": {"must_not": [{"match": {"foo": "bar"}}]}}),
            (
                "foo:bar and (qux:mux or qux:tux)",
                {
                    "bool": {
                        "filter": [
                            {"match": {"foo": "bar"}},
                            {
                                "bool": {
                                    "minimum_should_match": 1,
                                    "should": [{"match": {"qux": "mux"}}, {"match": {"qux": "tux"}}],
                                }
                            },
                        ]
                    }
                },
            ),
            (
                "(foo:bar and qux:mux) or qux:tux",
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {
                                "bool": {
                                    "filter": [{"match": {"foo": "bar"}}, {"match": {"qux": "mux"}}],
                                }
                            },
                            {"match": {"qux": "tux"}},
                        ],
                    }
                },
            ),
            (
                "foo:bar and qux:mux and qux:tux",
                {
                    "bool": {
                        "filter": [
                            {"match": {"foo": "bar"}},
                            {"match": {"qux": "mux"}},
                            {"match": {"qux": "tux"}},
                        ]
                    }
                },
            ),
            (
                "foo:bar and qux:mux or qux:tux",
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {
                                "bool": {
                                    "filter": [{"match": {"foo": "bar"}}, {"match": {"qux": "mux"}}],
                                }
                            },
                            {"match": {"qux": "tux"}},
                        ],
                    }
                },
            ),
            (
                "foo:bar or qux:mux and qux:tux",
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {"match": {"foo": "bar"}},
                            {
                                "bool": {
                                    "filter": [{"match": {"qux": "mux"}}, {"match": {"qux": "tux"}}],
                                }
                            },
                        ],
                    }
                },
            ),
            (
                "foo:(bar or baz)",
                {"bool": {"minimum_should_match": 1, "should": [{"match": {"foo": "bar"}}, {"match": {"foo": "baz"}}]}},
            ),
            (
                "foo:(qux and (mux or tux))",
                {
                    "bool": {
                        "filter": [
                            {"match": {"foo": "qux"}},
                            {
                                "bool": {
                                    "minimum_should_match": 1,
                                    "should": [{"match": {"foo": "mux"}}, {"match": {"foo": "tux"}}],
                                }
                            },
                        ]
                    }
                },
            ),
            (
                "foo:(bar and not baz)",
                {"bool": {"filter": [{"match": {"foo": "bar"}}, {"bool": {"must_not": [{"match": {"foo": "baz"}}]}}]}},
            ),
            (
                "items:{ name:banana and stock:9 }",
                {
                    "nested": {
                        "path": "items",
                        "query": {
                            "bool": {
                                "filter": [
                                    {"match": {"items.name": "banana"}},
                                    {"match": {"items.stock": "9"}},
                                ]
                            }
                        },
                        "score_mode": "none",
                    },
                },
            ),
            (
                "items:{ name:banana } and items:{ stock:9 }",
                {
                    "bool": {
                        "filter": [
                            {
                                "nested": {
                                    "path": "items",
                                    "query": {
                                        "match": {"items.name": "banana"},
                                    },
                                    "score_mode": "none",
                                }
                            },
                            {
                                "nested": {
                                    "path": "items",
                                    "query": {
                                        "match": {"items.stock": "9"},
                                    },
                                    "score_mode": "none",
                                }
                            },
                        ]
                    }
                },
            ),
            (
                "items:{ name:banana and stock > 10 } and items:{ category:vegetable }",
                {
                    "bool": {
                        "filter": [
                            {
                                "nested": {
                                    "path": "items",
                                    "query": {
                                        "bool": {
                                            "filter": [
                                                {"match": {"items.name": "banana"}},
                                                {"range": {"items.stock": {"gt": "10"}}},
                                            ]
                                        }
                                    },
                                    "score_mode": "none",
                                },
                            },
                            {
                                "nested": {
                                    "path": "items",
                                    "query": {
                                        "match": {"items.category": "vegetable"},
                                    },
                                    "score_mode": "none",
                                },
                            },
                        ]
                    }
                },
            ),
        ],
    )
    def should_produce_expected_query(query: str, expected: dict):
        assert parse(query) == expected
