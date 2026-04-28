"""CLI entry point for running JobScout v1 against a single query."""
import sys
from v1.agent import build_graph


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m v1.run "your query here"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    graph = build_graph()
    result = graph.invoke(
        {"messages": [("user", query)]},
        config={"recursion_limit": 10},
    )

    print("\n=== JobScout v1 result ===\n")
    print(result["messages"][-1].content)
    print(f"\n=== {len(result['messages'])} messages in this run ===")


if __name__ == "__main__":
    main()
