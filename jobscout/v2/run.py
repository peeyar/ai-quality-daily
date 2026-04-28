"""CLI entry point for running JobScout v2 against a single query."""
import sys
from v2.agent import build_graph


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m v2.run "your query here"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    graph = build_graph()
    result = graph.invoke(
        {
            "messages": [("user", query)],
            "search_history": [],
            "fetched_urls": [],
        },
        config={"recursion_limit": 10},
    )

    print("\n=== JobScout v2 result ===\n")
    print(result["messages"][-1].content)
    print(f"\n=== {len(result['messages'])} messages ===")
    print(f"=== {len(result.get('search_history', []))} searches ===")
    print(f"=== {len(result.get('fetched_urls', []))} fetches ===")


if __name__ == "__main__":
    main()
