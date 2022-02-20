import sys

from elastic_log_cli.kql.parser import get_parser


def main():
    query = sys.argv[1]
    print(f"Got query {query!r}")
    parser = get_parser()
    print("Loaded parser")
    result = parser.parse(query)
    print(f"Result: {result.pretty()}")
    return result


if __name__ == "__main__":
    tree = main()
