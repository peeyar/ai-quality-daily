"""Fit analyzer subgraph for JobScout v5.

Reads the plan and the searcher's results. For each URL in plan.analyze_fit_for,
calls the CareerTailor MCP server to get a fit analysis. Asks an LLM to
rewrite the existing analyzer answer to incorporate the fit data.

Graceful degradation: if the MCP server is unreachable for any URL, that
URL's fit analysis is skipped. If ALL fit analyses fail, the existing answer
is returned unchanged with a note logged to stderr.

v5 difference from v4: the node body is wrapped in a `v5.fit_analyzer` span,
and each per-URL MCP call gets its own `v5.fit_analyzer.mcp_call` child span.
The parallel asyncio.gather structure is visible in Phoenix as sibling spans.
"""
import asyncio
import os
from typing import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph

from v5.instrumentation import get_tracer
from v5.schemas import Plan, SearcherResult, FinalAnswer, JobFitAnalysis
from v5.mcp_client import call_analyze_job_fit


tracer = get_tracer()


# Hard-coded for v5. In a multi-user product this would come from auth context.
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
            "[v5 fit_analyzer] V4_DEFAULT_USER_ID not set; skipping fit analysis"
        )
        return []

    async def analyze_one(url: str) -> JobFitAnalysis | None:
        with tracer.start_as_current_span("v5.fit_analyzer.mcp_call") as span:
            span.set_attribute("url", url)
            description = searcher_result.fetched_descriptions.get(url)
            if not description:
                print(
                    f"[v5 fit_analyzer] No fetched description for {url}; skipping"
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


FIT_ANSWER_PROMPT = """You are JobScout's fit-aware answerer. The user asked
about resume-vs-job fit. CareerTailor has already analyzed the user's master
resume against each job's full description and returned a structured FitAnalysis
for each one.

Your job: write the user-facing answer using ONLY the fit analyses below.
Each FitAnalysis contains real data from a real resume comparison:
- match_score (0-100)
- matching_keywords: skills the user HAS that match the job
- missing_keywords: skills the user LACKS that the job wants
- summary_reasoning: short explanation

Rules:
- Do NOT say "no resume was provided" or "I cannot evaluate your resume" —
  the resume IS available; CareerTailor used it to produce the scores below.
- Match the plan's answer_template format (e.g. "rank by fit", "list scores",
  "explain why poor fit").
- Be CONCISE.
- If the user asked about ranking, sort by match_score descending.
- If the user asked "why poor fit", focus on missing_keywords and reasoning.
- Cite the exact match_score for each job analyzed.
"""


def build_fit_analyzer_graph():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ["GEMINI_API_KEY"],
    )
    structured_llm = llm.with_structured_output(FinalAnswer, method="json_mode")

    def fit_analyzer_node(state: FitAnalyzerState):
        with tracer.start_as_current_span("v5.fit_analyzer"):
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
            # Build the answer from scratch using the fit analyses, not the
            # analyzer's existing (potentially wrong-framed) answer.
            context_lines = [
                f"USER INTENT: {plan.user_intent}",
                f"ANSWER TEMPLATE: {plan.answer_template}",
                "",
                "FIT ANALYSES:",
            ]
            for fa in fit_analyses:
                context_lines.append(
                    f"- {fa.url}: score {fa.match_score}/100"
                )
                context_lines.append(
                    f"  matching_keywords: {fa.matching_keywords}"
                )
                context_lines.append(
                    f"  missing_keywords: {fa.missing_keywords}"
                )
                context_lines.append(
                    f"  reasoning: {fa.summary_reasoning}"
                )

            messages = [
                SystemMessage(content=FIT_ANSWER_PROMPT),
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
