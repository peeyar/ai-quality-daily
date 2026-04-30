"""Parent graph state for JobScout v3.

This state is the orchestration contract — each subgraph reads from it and
writes to it via the parent graph's edges. The subgraphs themselves have
their own internal state.
"""
from typing import TypedDict
from v3.schemas import Plan, SearcherResult, FinalAnswer


class ParentState(TypedDict):
    user_query: str
    plan: Plan | None
    searcher_result: SearcherResult | None
    final_answer: FinalAnswer | None
