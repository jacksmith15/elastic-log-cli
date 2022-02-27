from functools import cache
from pathlib import Path

from lark import Lark, Token, Transformer, Tree


# TODO: Multi-field
# TODO: Field-awareness
# TODO: Value-lists `field:(value or othervalue)`
# TODO: Nested query
# TODO: Sub-query
# TODO: Escape stripping


@cache
def get_parser():
    with open(Path(__file__).parent / "kql.grammar", "r", encoding="utf-8") as file:
        content = file.read()
    return Lark(content)

class KQLTreeTransformer(Transformer):

    def start(self, body) -> dict:
        return body[0]

    def query(self, terms) -> dict:
        return {"query": terms}

    def not_query(self, operands: list) -> dict:
        return {
            "bool": {
                "must_not": operands[-1]
            }
        }

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

    def value_expression(self, values: list[Tree]) -> dict:
        return {"exists": {"field": values[0]}}

    def field_value_expression(self, terms) -> dict:
        field, expression = terms
        if isinstance(expression, str):
            if expression == "*":
                return {"exists": {"field": field}}
            return {
                "match": {
                    field: expression
                }
            }
        else:
            raise NotImplementedError
        return [field, expression]

    def field_range_expression(self, terms) -> dict:
        field, operator, value = terms
        operator = {
            "<=": "lte",
            ">=": "gte",
            "<": "lt",
            ">": "gt"
        }[operator]
        return {
            "range": {
                field: {operator: value}
            }
        }

    def field(self, values: list[Token]) -> str:
        return str(values[0])

    def value(self, values: list[Token]) -> str:
        return str(values[0])

    def unquoted_literal(self, values: list[Token]) -> str:
        return "".join(values)


def parse(string: str) -> Tree:
    return get_parser().parse(string)


def transform(tree: Tree) -> dict:
    return KQLTreeTransformer().transform(tree)
