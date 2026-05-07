"""Searcher subgraph for JobScout v5.

Reads a Plan, executes the searches and direct fetches, returns aggregated
results. No LLM here — pure execution logic. The intelligence happened in
the planner; the searcher just runs the plan.

v5 difference from v4: the node body is wrapped in a `v5.searcher` span so
Phoenix shows the searcher as a distinct child of the orchestrator span.
"""
from typing import TypedDict
from langgraph.graph import StateGraph

from v5.instrumentation import get_tracer
from v5.schemas import Plan, SearcherResult, JobSearchResult
from v5.search_adapter import structured_search
from shared.mock_jobs import mock_fetch


tracer = get_tracer()


class SearcherState(TypedDict):
    plan: Plan
    result: SearcherResult | None


def build_searcher_graph():
    def searcher_node(state: SearcherState):
        with tracer.start_as_current_span("v5.searcher"):
            plan = state["plan"]
            all_hits: list[JobSearchResult] = []
            seen_urls: set[str] = set()
            empty_queries = []
            fetched: dict[str, str] = {}

            # Run each structured search
            for q in plan.search_queries:
                results = structured_search(q)
                if results.total_found == 0:
                    empty_queries.append(q)
                for hit in results.matches:
                    if hit.url not in seen_urls:
                        seen_urls.add(hit.url)
                        all_hits.append(hit)

            # Run each direct fetch from the user's URLs
            for url in plan.direct_fetches:
                fetched[url] = mock_fetch(url)

            # Also fetch descriptions for search hits if the plan has post-fetch filters
            # (the analyzer will need the full text to filter on salary, requirements, etc.)
            if plan.post_fetch_filters:
                for hit in all_hits:
                    if hit.url not in fetched:
                        fetched[hit.url] = mock_fetch(hit.url)

            return {
                "result": SearcherResult(
                    search_hits=all_hits,
                    fetched_descriptions=fetched,
                    empty_queries=empty_queries,
                )
            }

    graph = StateGraph(SearcherState)
    graph.add_node("execute", searcher_node)
    graph.set_entry_point("execute")
    graph.set_finish_point("execute")
    return graph.compile()
