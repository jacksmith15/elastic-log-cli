import json
import sys

from elastic_log_cli.kql.parser import get_parser, parse, transform


def main():
    query = sys.argv[1]
    print(f"Got query {query!r}")
    get_parser()
    print("Loaded parser")
    tree = parse(query)
    print(f"Tree:\n{tree.pretty()}")
    result = transform(tree)
    print(f"Result:\n{json.dumps(result, indent=2)}")
    return tree, result


if __name__ == "__main__":
    tree, result = main()
