"""Fit analyzer subgraph for JobScout v4.

Reads the plan and the searcher's results. For each URL in plan.analyze_fit_for,
calls the CareerTailor MCP server to get a fit analysis. Asks an LLM to
rewrite the existing analyzer answer to incorporate the fit data.

Graceful degradation: if the MCP server is unreachable for any URL, that
URL's fit analysis is skipped. If ALL fit analyses fail, the existing answer
is returned unchanged with a note logged to stderr.
"""
import asyncio
import os
from typing import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph

from v4.schemas import Plan, SearcherResult, FinalAnswer, JobFitAnalysis
from v4.mcp_client import call_analyze_job_fit


# Hard-coded for v4. In a multi-user product this would come from auth context.
DEFAULT_USER_ID = os.environ.get("V4_DEFAULT_USER_ID", "")


class FitAnalyzerState(TypedDict):
    plan: Plan
    searcher_result: SearcherResult
    final_answer: FinalAnswer
    fit_analyses: list[JobFitAnalysis]


async def _gather_fit_analyses(
    plan: Plan,
    searcher_result: SearcherResult,
) -> list[JobFitAnalysis]:
    """For each URL in plan.analyze_fit_for, call the MCP server.

    Uses asyncio.gather for parallel calls. Skips URLs whose descriptions
    weren't fetched.
    """
    if not DEFAULT_USER_ID:
        print(
            "[v4 fit_analyzer] V4_DEFAULT_USER_ID not set; skipping fit analysis"
        )
        return []

    async def analyze_one(url: str) -> JobFitAnalysis | None:
        description = searcher_result.fetched_descriptions.get(url)
        if not description:
            print(
                f"[v4 fit_analyzer] No fetched description for {url}; skipping"
            )
            return None
        result = await call_analyze_job_fit(
            user_id=DEFAULT_USER_ID,
            job_description=description,
        )
        if result is None:
            return None
        return JobFitAnalysis(
            url=url,
            match_score=result["match_score"],
            matching_keywords=result["matching_keywords"],
            missing_keywords=result["missing_keywords"],
            summary_reasoning=result["summary_reasoning"],
        )

    tasks = [analyze_one(url) for url in plan.analyze_fit_for]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


ENRICHMENT_PROMPT = """You are JobScout's fit-aware answerer.

You have:
- An EXISTING ANSWER that was already produced by the analyzer
- A list of FIT ANALYSES from CareerTailor for specific jobs

Rewrite the existing answer to incorporate the fit analyses. Add fit scores
and a short comment about matching/missing keywords for each analyzed job.
Keep the same structure and detail level as the existing answer. Be CONCISE.

If the FIT ANALYSES list is empty, return the existing answer unchanged.
"""


def build_fit_analyzer_graph():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ["GEMINI_API_KEY"],
    )
    structured_llm = llm.with_structured_output(FinalAnswer, method="json_mode")

    def fit_analyzer_node(state: FitAnalyzerState):
        plan = state["plan"]
        searcher_result = state["searcher_result"]
        existing_answer = state["final_answer"]

        # Run async fit analysis from sync LangGraph node
        fit_analyses = asyncio.run(_gather_fit_analyses(plan, searcher_result))

        # If no fit analyses came back, return the existing answer unchanged
        if not fit_analyses:
            return {
                "final_answer": existing_answer,
                "fit_analyses": [],
            }

        # Otherwise, ask the LLM to enrich the existing answer
        context_lines = [
            f"EXISTING ANSWER:\n{existing_answer.answer}",
            "",
            "FIT ANALYSES:",
        ]
        for fa in fit_analyses:
            context_lines.append(
                f"- {fa.url}: score {fa.match_score}/100, "
                f"matches {fa.matching_keywords[:3]}, "
                f"missing {fa.missing_keywords[:3]}, "
                f"summary: {fa.summary_reasoning}"
            )

        messages = [
            SystemMessage(content=ENRICHMENT_PROMPT),
            HumanMessage(content="\n".join(context_lines)),
        ]
        enriched = structured_llm.invoke(messages)
        return {
            "final_answer": enriched,
            "fit_analyses": fit_analyses,
        }

    graph = StateGraph(FitAnalyzerState)
    graph.add_node("enrich", fit_analyzer_node)
    graph.set_entry_point("enrich")
    graph.set_finish_point("enrich")
    return graph.compile()
