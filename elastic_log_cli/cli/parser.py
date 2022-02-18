import re
from datetime import datetime
from collections.abc import Iterator
from typing import NamedTuple, NoReturn

from elastic_log_cli.exceptions import ElasticLogError, ElasticLogValidationError


def build_query(specifiers: tuple[str, ...], *, start: datetime, end: datetime | None, timestamp_field: str):
    """Convert CLI arguments into an ES query."""
    time_filter = {"range": {timestamp_field: {"gte": start.isoformat()}}}
    if end:
        time_filter["range"][timestamp_field]["lte"] = end.isoformat()
    return {
        "bool": {
            "must": [
                time_filter,
                *map(parse_specifier, specifiers),
            ]
        }
    }


OPERATORS = {
    "equals": "=",
    "less_than": "<",
    "greater_than": ">",
    "match": "~",
}


TOKENS = {
    **{name: rf"(?<!\\){re.escape(operator)}" for name, operator in OPERATORS.items()},
    "term": r".+?",
}

TOKEN_REGEX = re.compile("|".join(f"(?P<{token_type}>{regex})" for token_type, regex in TOKENS.items()))


class Token(NamedTuple):
    type: str
    value: str


def parse_specifier(specifier: str) -> dict:
    """Parse a given specifier.

    This can be just a field name (exists query), or <fieldname><operator><value>.

    For example "http.status>499" means get all docs where the HTTP status code is greater than 499.
    """
    tokens = list(tokenize_specifier(specifier))
    if len(tokens) == 1:
        token = tokens[0]
        if token.type != "term":
            raise_for_specifier(specifier, tokens)
        return {"exists": {"field": token.value}}
    if len(tokens) == 3:
        types = [token.type for token in tokens]
        if not (
            types[0] == "term"
            and types[1] in OPERATORS
            and types[2] == "term"
        ):
            raise_for_specifier(specifier, tokens)

        field = tokens[0].value
        operator = tokens[1]
        value = tokens[2].value

        if operator.type == "equals":
            return {
                "term": {field: {"value": value}}
            }
        if operator.type == "less_than":
            return {
                "range": {field: {"lt": value}}
            }
        if operator.type == "greater_than":
            return {
                "range": {field: {"gt": value}}
            }
        if operator.type == "match":
            if value.endswith("*"):
                value = value.removesuffix("*")
                return {
                    "match_phrase_prefix": {field: {"query":  value}}
                }
            return {
                "match": {field: {"query": value}}
            }
        raise ElasticLogError(f"Unknown operator {operator.type!r}.")
    raise_for_specifier(specifier, tokens)
    assert False, f"Unexpected number of tokens: {tokens}"


def raise_for_specifier(specifier: str, tokens: list[Token]) -> NoReturn:
    raise ElasticLogValidationError(
        f"""Invalid specifier {specifier!r}:
    Tokens: {[token.value for token in tokens]}

    A specifier can either be a single field name (for exists), or a field name, operator and value.
    The available operators are {list(OPERATORS.values())}.
    Escape them with '\\' to use them in a field name or value.
"""
    )


def tokenize_specifier(specifier) -> Iterator[Token]:
    term = ""
    for match in re.finditer(TOKEN_REGEX, specifier):
        assert match.lastgroup
        if match.lastgroup == "term":
            term = term + match.group()
        else:
            if term:
                yield Token(type="term", value=unescape(term))
            yield Token(type=match.lastgroup, value=unescape(match.group()))
            term = ""
    if term:
        yield Token(type="term", value=unescape(term))


def unescape(term: str) -> str:
    for operator in OPERATORS.values():
        term = re.sub(rf"\\{operator}", operator, term)
    return term
