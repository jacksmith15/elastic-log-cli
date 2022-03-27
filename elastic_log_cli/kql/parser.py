"""KQL Parser.

Based on https://github.com/elastic/kibana/tree/614139b8e5a38c60918586c2282eb75c88fedb80/packages/kbn-es-query
"""
import json
from functools import cache
from pathlib import Path

from lark import Lark, Token, Transformer, Tree

# TODO: Multi-field (e.g. *:value)
# TODO: Field-awareness
# TODO: Multi-nested query (using field awareness?)
# TODO: Wildcards for prefix matching on values
# TODO: Wildcards for prefix matching (including sub-fields) on fields


@cache
def get_parser():
    with open(Path(__file__).parent / "kql.grammar", "r", encoding="utf-8") as file:
        content = file.read()
    return Lark(content)


class KQLTreeTransformer(Transformer):
    def start(self, body) -> dict:
        return body[0]

    def query(self, terms) -> dict:
        assert len(terms) == 1
        return terms[0]

    def not_query(self, operands: list) -> dict:
        return {"bool": {"must_not": [operands[-1]]}}

    def and_query(self, operands: list) -> dict:
        return {
            "bool": {
                "filter": operands,
            }
        }

    def or_query(self, operands: list) -> dict:
        return {
            "bool": {
                "should": operands,
                "minimum_should_match": 1,
            }
        }

    def nested_query(self, terms: list) -> dict:
        field, query = terms
        _apply_field_prefix(field, query)
        return {"nested": {"path": field, "query": query, "score_mode": "none"}}

    def value_expression(self, values: list[Tree]) -> dict:
        return {"exists": {"field": values[0]}}

    def field_value_expression(self, terms) -> dict:
        field, expression = terms
        if isinstance(expression, str):
            if expression == "*":
                return {"exists": {"field": field}}
            return {"match": {field: expression}}
        elif isinstance(expression, Tree):
            expression_type = expression.data.value  # type: ignore[attr-defined]
            constructor = {
                "or_list_of_values": self.or_query,
                "and_list_of_values": self.and_query,
                "not_list_of_values": self.not_query,
            }[expression_type]
            return constructor([self.field_value_expression([field, value]) for value in expression.children])
        raise NotImplementedError

    def field_range_expression(self, terms) -> dict:
        field, operator, value = terms
        operator = {"<=": "lte", ">=": "gte", "<": "lt", ">": "gt"}[operator]
        return {"range": {field: {operator: value}}}

    def field(self, values: list[Token]) -> str:
        return str(values[0])

    def value(self, values: list[Token]) -> str:
        return str(values[0])

    def quoted_string(self, values: list) -> str:
        assert len(values) == 1
        string = values[0]
        return json.loads(string)

    def unquoted_literal(self, tokens: list[Token]) -> str:
        return "".join(tokens)

    def unquoted_character(self, tokens: list[Token]) -> str:
        assert len(tokens) == 1
        token = tokens[0]
        token_type = token.type
        value = token.value
        if token_type == "ESCAPED_WHITESPACE":
            return {"\\t": "\t", "\\r": "\r", "\\n": "\n"}[value]
        if token_type in ("ESCAPED_SPECIAL_CHARACTER", "ESCAPED_KEYWORD"):
            return value[1:]
        if token_type == "ESCAPED_UNICODE_SEQUENCE":
            return value.encode("utf-8").decode("unicode-escape")
        return value


def parse(string: str) -> dict:
    return transform(get_parser().parse(string))


def transform(tree: Tree) -> dict:
    return KQLTreeTransformer().transform(tree)


def _apply_field_prefix(prefix: str, query: dict) -> None:
    """Nasty mutating recursive function to apply nested query prefixes.

    KQL doesn't include the prefix, e.g.

        items:{ name:banana }

    becomes

        {"path": "items", "query": {"match": {"items.name": "banana"}}}

    but the grammar inside `{}` doesn't have that context.
    """
    if "bool" in query:
        for operator in ["must", "filter", "should", "must_not"]:
            for subquery in query["bool"].get(operator, []):
                _apply_field_prefix(prefix, subquery)
        return
    if "nested" in query:
        query["nested"]["path"] = f"{prefix}.{query['nested']['path']}"
        _apply_field_prefix(prefix, query["nested"]["query"])
    if "exists" in query:
        query["exists"]["field"] = f"{prefix}.{query['exists']['field']}"
    for query_type in ["match", "range"]:
        if query_type in query:
            field, value = query[query_type].popitem()
            query[query_type][f"{prefix}.{field}"] = value
