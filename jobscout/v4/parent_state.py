"""Parent graph state for JobScout v4.

This state is the orchestration contract — each subgraph reads from it and
writes to it via the parent graph's edges. The subgraphs themselves have
their own internal state.

v4 adds `fit_analyses` — populated only when plan.analyze_fit_for is non-empty.
"""
from typing import TypedDict
from v4.schemas import Plan, SearcherResult, FinalAnswer, JobFitAnalysis


class ParentState(TypedDict):
    user_query: str
    plan: Plan | None
    searcher_result: SearcherResult | None
    final_answer: FinalAnswer | None
    fit_analyses: list[JobFitAnalysis]
