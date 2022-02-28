from functools import cache
from pathlib import Path

from lark import Lark, Token, Transformer, Tree


# TODO: Multi-field
# TODO: Field-awareness
# TODO: Nested query
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
        assert len(terms) == 1
        return terms[0]

    def not_query(self, operands: list) -> dict:
        return {
            "bool": {
                "must_not": [operands[-1]]
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
        elif isinstance(expression, Tree):
            expression_type = expression.data.value  # type: ignore[attr-defined]
            constructor = {
                "or_list_of_values": self.or_query,
                "and_list_of_values": self.and_query,
                "not_list_of_values": self.not_query,
            }[expression_type]
            return constructor([self.field_value_expression([field, value]) for value in expression.children])
        print(expression)
        raise NotImplementedError

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

    def quoted_string(self, values: list) -> str:
        assert len(values) == 1
        string = values[0]
        string = string.removeprefix('"')
        string = string.removesuffix('"')
        return string

    def unquoted_literal(self, values: list[Token]) -> str:
        return "".join(values)


def parse(string: str) -> dict:
    return transform(get_parser().parse(string))


def transform(tree: Tree) -> dict:
    return KQLTreeTransformer().transform(tree)
