"""Analyzer subgraph for JobScout v3.

Reads the plan and the searcher's result. Applies post-fetch filters
that needed the full job description text. Produces the final answer.

Uses an LLM for the final answer formatting because turning structured
data into prose is what LLMs are good at — but the LLM does NOT make
decisions about what to include. The plan + filters do that.
"""
import os
from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph

from v3.schemas import Plan, SearcherResult, FinalAnswer


ANALYZER_SYSTEM_PROMPT = """You are JobScout's ANALYZER. You produce the final
user-facing answer.

Inputs:
- The PLAN that the planner produced
- The SEARCHER_RESULT with search hits and fetched job descriptions

Your job:
1. If the plan has post_fetch_filters, apply them by reading each fetched
   description and checking if it satisfies the filter. Drop jobs that don't.
2. Format the surviving jobs according to the plan's answer_template.
3. If post_fetch_filters required information NOT present in the descriptions,
   say so clearly. Do not invent data.
4. If no jobs survive filtering, say so cleanly. Do not pretend you found something.

Be CONCISE. Match the answer_template's format. No preamble like "I found...".
"""


class AnalyzerState(TypedDict):
    plan: Plan
    searcher_result: SearcherResult
    final_answer: FinalAnswer | None


def build_analyzer_graph():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ["GEMINI_API_KEY"],
    )
    # Match the planner's structured-output method for consistency. (FinalAnswer
    # itself is union-free, but using the same method keeps schema-handling
    # behavior identical across the two LLM-bearing subgraphs.)
    structured_llm = llm.with_structured_output(FinalAnswer, method="json_mode")

    def analyzer_node(state: AnalyzerState):
        plan = state["plan"]
        result = state["searcher_result"]

        # Build a context string the LLM can read
        context_parts = [
            f"USER INTENT: {plan.user_intent}",
            f"ANSWER TEMPLATE: {plan.answer_template}",
            f"POST-FETCH FILTERS: {[f.model_dump() for f in plan.post_fetch_filters]}",
            f"\nSEARCH HITS ({len(result.search_hits)}):",
        ]
        for hit in result.search_hits:
            context_parts.append(f"  - {hit.title} at {hit.company} ({hit.url})")

        if result.fetched_descriptions:
            context_parts.append(f"\nFETCHED DESCRIPTIONS:")
            for url, desc in result.fetched_descriptions.items():
                context_parts.append(f"\n--- {url} ---\n{desc}")

        if result.empty_queries:
            context_parts.append(
                f"\nNOTE: {len(result.empty_queries)} search queries returned no results."
            )

        context = "\n".join(context_parts)

        messages = [
            SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]
        answer = structured_llm.invoke(messages)
        return {"final_answer": answer}

    graph = StateGraph(AnalyzerState)
    graph.add_node("analyze", analyzer_node)
    graph.set_entry_point("analyze")
    graph.set_finish_point("analyze")
    return graph.compile()
