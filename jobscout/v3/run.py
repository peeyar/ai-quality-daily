"""CLI entry point for JobScout v3."""
import sys
from dotenv import load_dotenv
from v3.orchestrator import build_graph


def main():
    load_dotenv()
    if len(sys.argv) < 2:
        print('Usage: python -m v3.run "your query here"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    graph = build_graph()
    result = graph.invoke({
        "user_query": query,
        "plan": None,
        "searcher_result": None,
        "final_answer": None,
    })

    print("\n=== JobScout v3 result ===\n")
    print(result["final_answer"].answer)

    plan = result["plan"]
    sr = result.get("searcher_result")
    print(f"\n=== Plan: {len(plan.search_queries)} searches, "
          f"{len(plan.direct_fetches)} fetches, "
          f"{len(plan.post_fetch_filters)} filters ===")
    if sr:
        print(f"=== Searcher: {len(sr.search_hits)} hits, "
              f"{len(sr.fetched_descriptions)} fetched, "
              f"{len(sr.empty_queries)} empty queries ===")
    if plan.refusal_reason:
        print(f"=== REFUSED: {plan.refusal_reason} ===")


if __name__ == "__main__":
    main()
