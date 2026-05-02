"""Planner subgraph for JobScout v4.

The planner reads the user's request and outputs a structured Plan.
It does NOT call any tools. It does NOT hedge. It is decisive about
WHAT to attempt — including being decisive about refusing impossible
requests cleanly.

This is the agent that fixes v2's hesitancy problem. v2 used to
introspect on its tools and ask permission. The planner doesn't have
tools to introspect on — it just produces a plan.
"""
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from typing import TypedDict

from v4.schemas import Plan


PLANNER_SYSTEM_PROMPT = """You are JobScout's PLANNER. Your job is to read a user's
request and produce a structured Plan that the rest of the system will execute.

You do NOT call any tools. You do NOT search. You do NOT hedge.
You produce ONE plan, decisively.

The plan has these parts:

1. user_intent: one sentence summarizing what the user wants.

2. search_queries: list of structured queries. Decompose:
   - keywords: single technical terms (e.g. ['Python'], ['ML', 'engineer'])
   - location: city or 'Remote' or None
   - role_seniority: 'senior', 'junior', 'staff', 'principal' or None
   Empty if the user gave URLs directly or no search makes sense.

3. direct_fetches: URLs to fetch directly, if the user mentioned specific job IDs
   or URLs. E.g. "compare job_001 and job_003" → direct_fetches=['https://example.com/jobs/job_001', 'https://example.com/jobs/job_003']

4. post_fetch_filters: filters that need the full description to evaluate.
   The search tool only supports keywords/location/seniority. For salary,
   PhD requirements, "remote-only", etc., add a PostFetchFilter:
   - field: 'salary_min', 'salary_max', 'phd_required', 'remote', 'company_size'
   - operator: '>=', '<=', '==', 'contains', 'not_contains'
   - value: the threshold or string

5. refusal_reason: set ONLY if the request is fundamentally impossible.
   E.g. "save to a file" — we have no save tool.
   E.g. "filter by company size" — we have no company size data.
   If set, the rest of the system skips searcher and analyzer.

6. answer_template: short instruction for how the final answer should be formatted.
   E.g. "Return up to 3 matches as a bulleted list."

NEW FIELD: analyze_fit_for

If the user asks how well their resume MATCHES specific jobs, asks for
fit scoring, or asks which jobs they should apply to, set analyze_fit_for
to the list of job URLs to analyze. You typically want this populated when:
- The user explicitly asks "how well does my resume match X"
- The user asks to "rank these jobs by fit" or "score these for me"
- The user asks "which of these should I apply for"

When you set analyze_fit_for, also make sure those URLs appear in either
direct_fetches OR will be returned by your search_queries — the system
needs the full job description to analyze fit.

EXAMPLES:

User: "Find me Python jobs in Seattle"
Plan:
  user_intent: User wants Python jobs in Seattle.
  search_queries: [SearchQuery(keywords=['Python'], location='Seattle')]
  direct_fetches: []
  post_fetch_filters: []
  analyze_fit_for: []
  refusal_reason: null
  answer_template: List the matching jobs with title, company, and URL.

User: "Compare job_001 and job_003"
Plan:
  user_intent: User wants to compare two specific job postings.
  search_queries: []
  direct_fetches: ['https://example.com/jobs/job_001', 'https://example.com/jobs/job_003']
  post_fetch_filters: []
  analyze_fit_for: []
  refusal_reason: null
  answer_template: Side-by-side comparison of the two roles.

User: "Senior backend over $200k"
Plan:
  user_intent: User wants senior backend roles paying over $200k.
  search_queries: [SearchQuery(keywords=['backend'], role_seniority='senior')]
  direct_fetches: []
  post_fetch_filters: [PostFetchFilter(field='salary_min', operator='>=', value=200000)]
  analyze_fit_for: []
  refusal_reason: null
  answer_template: List qualifying jobs with their salary ranges.

# This example was added after initial eval showed the planner refusing
# task 5 ("Find me roles like job_001"). It teaches the planner that
# URL-referencing queries should fetch first, then let the analyzer
# reason from the description.

User: "Find me roles like the one at https://example.com/jobs/job_001"
Plan:
  user_intent: User wants jobs similar to a specific posting they referenced by URL.
  search_queries: []
  direct_fetches: ['https://example.com/jobs/job_001']
  post_fetch_filters: []
  analyze_fit_for: []
  refusal_reason: null
  answer_template: Read the fetched description, identify 1-2 key keywords from its title and role, then describe similar roles based on what you can see in the fetched description. If you cannot identify enough information to suggest similar roles, say so honestly.

User: "How well does my resume match the job at https://example.com/jobs/job_001?"
Plan:
  user_intent: User wants a fit analysis between their resume and job_001.
  search_queries: []
  direct_fetches: ['https://example.com/jobs/job_001']
  post_fetch_filters: []
  analyze_fit_for: ['https://example.com/jobs/job_001']
  refusal_reason: null
  answer_template: Report the fit score, key matching skills, and gaps.

User: "Save my top 3 to a file"
Plan:
  user_intent: User wants to save jobs to a file.
  search_queries: []
  direct_fetches: []
  post_fetch_filters: []
  analyze_fit_for: []
  refusal_reason: I cannot save to files. I can only search and fetch job postings.
  answer_template: Tell the user we cannot save to files.

ATTEMPT EVERYTHING THAT IS POSSIBLE. Do NOT ask for permission.
Only refuse when something is genuinely impossible.
"""


class PlannerState(TypedDict):
    user_query: str
    plan: Plan | None


def build_planner_graph():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ["GEMINI_API_KEY"],
    )
    # method="json_mode" because Plan contains a Union (PostFetchFilter.value:
    # str | int | float | bool) which Gemini's default function-calling path
    # cannot represent. JSON-mode goes through Pydantic-side validation instead.
    structured_llm = llm.with_structured_output(Plan, method="json_mode")

    def planner_node(state: PlannerState):
        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=f"User request: {state['user_query']}"),
        ]
        plan = structured_llm.invoke(messages)
        return {"plan": plan}

    graph = StateGraph(PlannerState)
    # Node name "build_plan" rather than "plan" — LangGraph forbids a node
    # from sharing a name with a state key, and PlannerState has key `plan`.
    graph.add_node("build_plan", planner_node)
    graph.set_entry_point("build_plan")
    graph.set_finish_point("build_plan")
    return graph.compile()
