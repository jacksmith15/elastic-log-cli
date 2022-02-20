from functools import cache
from pathlib import Path

from lark import Lark, Tree


@cache
def get_parser():
    with open(Path(__file__).parent / "kql.grammar", "r", encoding="utf-8") as file:
        content = file.read()
    return Lark(content)


def parse(string: str) -> Tree:
    return get_parser().parse(string)


def to_elasticsearch_query(
    tree: Tree,
    filters_in_must_clause: bool = False,
) -> dict:
    token = tree.data
    if token.type == "RULE":
        if token.value == "start":
            query = [subtree for subtree in tree.children if subtree.token.value == "query"]
            assert len(query) == 1
            return to_elasticsearch_query(query[0])
