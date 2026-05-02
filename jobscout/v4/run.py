"""CLI entry point for JobScout v4."""
import sys
from dotenv import load_dotenv

# Load .env BEFORE importing v4 modules — fit_analyzer reads V4_DEFAULT_USER_ID
# at module level, so the env must already be loaded by then.
load_dotenv()

from v4.orchestrator import build_graph

def main():
    if len(sys.argv) < 2:
        print('Usage: python -m v4.run "your query here"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    graph = build_graph()
    result = graph.invoke({
        "user_query": query,
        "plan": None,
        "searcher_result": None,
        "final_answer": None,
        "fit_analyses": [],
    })

    print("\n=== JobScout v4 result ===\n")
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

    fa = result.get("fit_analyses", [])
    if fa:
        print(f"=== Fit analyses: {len(fa)} ===")
        for f in fa:
            print(f"   {f.url}: {f.match_score}/100")


if __name__ == "__main__":
    main()
