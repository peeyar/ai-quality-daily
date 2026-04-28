# JobScout v1 — Build Spec for Cursor / Claude Code

**Goal:** Generate a working single-agent JobScout in LangGraph. Two tools, ReAct loop, 10-task test runner. Clean folder structure ready to publish.

**Stack:** Python 3.11+, LangGraph, LangChain, `langchain-google-genai`, Pydantic v2, `python-dotenv`, `pytest`.

**LLM:** Gemini 2.5 Flash (`gemini-2.5-flash`), `temperature=0`.

**Time budget:** This is one focused session. Don't over-engineer — v1 is the baseline we beat in v2–v7.

---

## Where you are in the repo

You are working inside `ai-quality-daily/jobscout/`. The folder structure already exists (scaffolded). Do not create the structure — just fill in the empty / stub files.

```
ai-quality-daily/
└── jobscout/                      ← you are here
    ├── pyproject.toml             ← already exists, has all deps for v1
    ├── .env.example               ← already exists
    ├── README.md                  ← already exists, do not modify
    ├── shared/
    │   ├── __init__.py            ← already exists, empty
    │   └── mock_jobs.py           ← STUB — fill in MOCK_JOBS, mock_search, mock_fetch
    └── v1/
        ├── README.md              ← already exists, do not modify
        ├── SPEC.md                ← this file
        └── (everything else needs to be created)
```

**Do not touch anything outside `jobscout/`.** CareerTailor is a sibling project — leave it alone.

---

## What to build

A LangGraph agent that takes a natural-language job-search query, decides when to call `search_jobs` or `fetch_description`, and returns a clean answer. Mock the tools (no real APIs in v1). Add a runner that executes a fixed 10-task test set and prints a pass/fail summary.

---

## Files to create (all under `v1/`)

```
v1/
├── __init__.py             ← empty
├── state.py                ← JobScoutState TypedDict
├── tools.py                ← @tool functions wrapping shared/mock_jobs
├── agent.py                ← build_graph() returning compiled LangGraph
├── run.py                  ← CLI entry: python -m v1.run "query"
└── tests/
    ├── __init__.py         ← empty
    ├── tasks.py            ← the 10 test tasks as a list
    └── run_tasks.py        ← runs all 10, prints pass/fail summary
```

---

## Files to FILL IN (already exist as stubs)

### `shared/mock_jobs.py`

Already has function signatures. Fill in:

- `MOCK_JOBS` — about 15 mock job postings with deliberate variety:
  - Different roles: Python engineer, ML engineer, backend engineer, data scientist, frontend, DevOps
  - Different locations: Seattle, SF, NYC, remote, hybrid
  - Different salaries: some explicit ranges, some missing entirely
  - Some tricky cases: oddly-named companies, missing remote field, missing salary
  - At least 2 jobs that mention "no PhD required" in description
  - At least 2 jobs at named "startup" or small companies
- `mock_search(query: str) -> list[dict]`:
  - Naive substring match on query against title + location + description
  - Lowercase comparison
  - Return up to 5 results
  - **Returns only `{title, company, url}`** — NO salary, NO description, NO remote status
  - This is deliberate — forces the agent to call `mock_fetch` for details
- `mock_fetch(url: str) -> str`:
  - Look up the URL in MOCK_JOBS
  - Return a multi-line string with: title, company, location, remote status, salary range (if available), full description
  - Return a "Job not found" string if URL doesn't match

---

## File-by-file requirements (new files)

### `v1/__init__.py`

Empty file.

### `v1/state.py`

```python
"""Agent state for JobScout v1.

v1 keeps state minimal — just the message history. add_messages appends
new messages to the list (instead of replacing it) which is how the agent
loop accumulates context across tool calls and LLM responses.
"""
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class JobScoutState(TypedDict):
    messages: Annotated[list, add_messages]
```

### `v1/tools.py`

Wrap the shared mocks with `@tool` decorators. Docstrings matter — the LLM reads them to decide when to call each tool.

```python
"""Tools available to JobScout v1. Two of them — search and fetch."""
from langchain_core.tools import tool
from shared.mock_jobs import mock_search, mock_fetch


@tool
def search_jobs(query: str) -> list[dict]:
    """Search for jobs matching a natural-language query.

    Returns up to 5 results with title, company, and URL only. No salary,
    no description, no remote status — call fetch_description for those.

    Use this first when looking for jobs.
    """
    return mock_search(query)


@tool
def fetch_description(url: str) -> str:
    """Fetch the full job description for a single job posting URL.

    Returns the description text including salary, remote status, and
    requirements. Call this after search_jobs when you need details
    that aren't in the search results.
    """
    return mock_fetch(url)
```

### `v1/agent.py`

```python
"""JobScout v1 — single LangGraph agent with ReAct loop."""
import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from v1.state import JobScoutState
from v1.tools import search_jobs, fetch_description

load_dotenv()

SYSTEM_PROMPT = """You are JobScout, an agent that helps users find jobs.

You have two tools:
- search_jobs: search for jobs by natural-language query
- fetch_description: get the full description for a single job URL

Search first. Fetch descriptions only when you need details the search results
don't include (like salary, remote status, or requirements).

When you have enough information, summarize the matching jobs clearly and stop
calling tools. Do not invent salary, remote status, company size, or any detail
you haven't actually seen in tool output. If you can't find what the user asked
for, say so directly."""


def build_graph(max_steps: int = 10):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ["GEMINI_API_KEY"],
    )
    tools = [search_jobs, fetch_description]
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: JobScoutState):
        messages = state["messages"]
        # Inject system prompt only once at the start
        has_system = any(
            getattr(m, "type", None) == "system" for m in messages
        )
        if not has_system:
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(JobScoutState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile()
```

### `v1/run.py`

```python
"""CLI entry point for running JobScout v1 against a single query."""
import sys
from v1.agent import build_graph


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m v1.run "your query here"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    graph = build_graph()
    result = graph.invoke(
        {"messages": [("user", query)]},
        config={"recursion_limit": 10},
    )

    print("\n=== JobScout v1 result ===\n")
    print(result["messages"][-1].content)
    print(f"\n=== {len(result['messages'])} messages in this run ===")


if __name__ == "__main__":
    main()
```

### `v1/tests/__init__.py`

Empty file.

### `v1/tests/tasks.py`

```python
"""The 10-task informal test set for JobScout v1.

These are deliberately mixed: simple cases JobScout should handle cleanly,
filtered cases that need fetch calls, vague queries that test the loop's
exit conditions, and impossible cases (missing tools or missing data).

Reused across v1, v2, v3 to allow direct comparison.
"""

TASKS = [
    {
        "id": 1,
        "query": "Find me Python jobs in Seattle",
        "category": "simple",
        "expected_behavior": "single search, return list",
    },
    {
        "id": 2,
        "query": "Find me 3 ML engineer roles at startups",
        "category": "filtered",
        "expected_behavior": "search then filter to 3 results",
    },
    {
        "id": 3,
        "query": "Senior backend roles paying over $200k",
        "category": "filtered_with_fetch",
        "expected_behavior": "search, fetch descriptions, filter by salary",
    },
    {
        "id": 4,
        "query": "Remote roles, no PhD required",
        "category": "filtered_with_fetch",
        "expected_behavior": "search, fetch, read requirements",
    },
    {
        "id": 5,
        "query": "Find me roles like the one at https://example.com/jobs/job_001",
        "category": "fetch_then_search",
        "expected_behavior": "fetch first, then search by similarity",
    },
    {
        "id": 6,
        "query": "Compare these two listings: job_001 and job_003",
        "category": "multi_fetch",
        "expected_behavior": "two fetches, structured comparison",
    },
    {
        "id": 7,
        "query": "What's hot in AI hiring this week?",
        "category": "vague",
        "expected_behavior": "should ask for clarification or interpret reasonably without infinite loop",
    },
    {
        "id": 8,
        "query": "Find me jobs but only at companies under 50 people",
        "category": "missing_metadata",
        "expected_behavior": "should admit company size is not in tool data",
    },
    {
        "id": 9,
        "query": "Senior MLE under $180k that don't require a PhD",
        "category": "multi_filter",
        "expected_behavior": "search, fetch, apply 3 filters at once",
    },
    {
        "id": 10,
        "query": "Save my top 3 to a file",
        "category": "missing_tool",
        "expected_behavior": "should refuse cleanly, no save tool exists",
    },
]
```

### `v1/tests/run_tasks.py`

Runs all 10, prints query + agent answer + message count for each. Pass/fail is **manual eyeballing** for v1 — no automated scoring yet (that lands in P6).

```python
"""Run all 10 tasks against JobScout v1 and print results.

Pass/fail is currently manual — eyeball each result against the
expected behavior. Automated scoring lands in P6 with the golden eval set.
"""
from v1.agent import build_graph
from v1.tests.tasks import TASKS


def run_all():
    graph = build_graph()
    results = []

    for task in TASKS:
        print(f"\n{'='*70}")
        print(f"Task {task['id']} ({task['category']})")
        print(f"Query:    {task['query']}")
        print(f"Expected: {task['expected_behavior']}")
        print('='*70)

        try:
            result = graph.invoke(
                {"messages": [("user", task["query"])]},
                config={"recursion_limit": 10},
            )
            answer = result["messages"][-1].content
            steps = len(result["messages"])
            print(f"\nAnswer:\n{answer}")
            print(f"\nMessages: {steps}")
            results.append({
                "task_id": task["id"],
                "steps": steps,
                "answer": answer,
                "error": None,
            })
        except Exception as e:
            print(f"\nERROR: {e}")
            results.append({"task_id": task["id"], "error": str(e)})

    return results


if __name__ == "__main__":
    results = run_all()
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    print(f"Total tasks: {len(results)}")
    print(f"Errored:     {sum(1 for r in results if r.get('error'))}")
    print(f"Completed:   {sum(1 for r in results if not r.get('error'))}")
    print("\nMark each task pass/fail manually based on the output above.")
```

---

## Acceptance criteria

After Cursor finishes, all of these must be true:

1. `poetry install` runs without errors
2. `poetry run python -m v1.run "Find me Python jobs in Seattle"` returns a sensible answer that references the mock data
3. `poetry run python -m v1.tests.run_tasks` runs all 10 tasks without crashing
4. Tool calls show up in the message history (verify by inspecting `result["messages"]`)
5. The agent uses both `search_jobs` and `fetch_description` across the 10 tasks
6. The recursion limit prevents infinite loops on task 7 (the vague query)
7. No file outside `jobscout/` is touched
8. Total Python LOC across `v1/` (excluding mock_jobs.py) is under 200 lines

---

## What NOT to build

These are explicitly out of scope for v1. Do not add them, even if they seem useful:

- Pydantic schemas on tool outputs (lands in P3 / v2)
- Long-term memory or vector storage (Bonus 2)
- Multi-agent setup (P4 / v3)
- MCP servers (P5 / v4)
- Phoenix tracing or DeepEval (P7 / v5)
- Real job board APIs (later, after v3)
- Streaming output, async, batching (P12)
- Guardrails, safety checks (P10)
- A web UI

If tempted to add any of these, stop. Each has a dedicated post.

---

## Style guide

- Type hints everywhere
- Docstrings on every public function (the `@tool` docstrings especially — the LLM reads them)
- One file = one concept (state, tools, agent, run)
- No clever metaprogramming. v1 should be readable by someone seeing LangGraph for the first time
- Comments explain *why*, not *what*
- Module docstrings at the top of every file

---

## Suggested invocation

In Cursor's Claude Code chat, after opening `ai-quality-daily/` as the workspace:

> Read `jobscout/v1/SPEC.md`. Build the v1 application exactly as specified. Fill in `jobscout/shared/mock_jobs.py` first with the mock data, then create all the files under `jobscout/v1/`. Do not touch anything outside `jobscout/`. After you finish, run `poetry install` from `jobscout/` and verify the acceptance criteria.

If Cursor asks clarifying questions, point it back to the relevant section of this spec. Don't let it wander.
