"""CLI entry point for JobScout v5."""
import sys
from dotenv import load_dotenv

# Critical ordering: load_dotenv first, register_phoenix second, v5 module
# imports third. Phoenix instrumentors must be active before LangChain agent
# code is loaded so spans capture LLM and MCP calls correctly.
load_dotenv()

from v5.instrumentation import register_phoenix
register_phoenix()

from v5.orchestrator import build_graph
from v5.instrumentation import get_tracer

_tracer = get_tracer()


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m v5.run "your query here"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    graph = build_graph()

    with _tracer.start_as_current_span("v5.orchestrator") as span:
        span.set_attribute("user_query", query)
        result = graph.invoke({
            "user_query": query,
            "plan": None,
            "searcher_result": None,
            "final_answer": None,
            "fit_analyses": [],
        })

    print("\n=== JobScout v5 result ===\n")
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
