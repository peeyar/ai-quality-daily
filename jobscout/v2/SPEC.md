# JobScout v2 — Build Spec for Cursor / Claude Code

**Goal:** Add structured outputs and short-term memory to JobScout. Same agent loop, same tools, same 10-task test set — but the agent now decomposes queries into structured fields and remembers what it has already tried.

**Stack:** Python 3.11+, LangGraph, LangChain, `langchain-google-genai`, **Pydantic v2** (heavy use), `python-dotenv`, `pytest`. All already in `pyproject.toml`.

**LLM:** Gemini 2.5 Flash (`gemini-2.5-flash`), `temperature=0`.

**Time budget:** This is the second focused session. v2 is meaningfully more code than v1 — budget 30-45 minutes for Cursor to complete.

---

## Where you are in the repo

You are working inside `ai-quality-daily/jobscout/`. The structure exists from v1.

```
ai-quality-daily/
└── jobscout/
    ├── pyproject.toml             ← already has everything v2 needs
    ├── shared/
    │   └── mock_jobs.py           ← do not modify, v2 uses the same data
    ├── v1/                        ← do not modify, frozen baseline
    └── v2/                        ← BUILD HERE
        └── (everything to be created)
```

**Critical rule: do not modify v1 or shared/.** v1 is the baseline we measure v2 against. Touching it invalidates the whole experiment.

---

## What's different from v1

Three concrete changes. Everything else stays the same.

### Change 1: Pydantic schemas force query decomposition

In v1, the `search_jobs` tool took `query: str`. The LLM passed full sentences. Strict matching killed it.

In v2, `search_jobs` takes a **structured** input — a Pydantic model with separate fields:

```python
class SearchQuery(BaseModel):
    keywords: list[str]  # e.g. ["Python", "Senior"]
    location: str | None  # e.g. "Seattle" or None
    role_type: str | None  # e.g. "engineer", "scientist"
```

The LLM now has to *decompose* the user's natural-language request into these fields. This is what changes everything.

Same for `fetch_description` — input is now a Pydantic model with a `url: str` field (overkill for a single field, but consistent with the pattern).

And tools **return** Pydantic models too:

```python
class JobSearchResult(BaseModel):
    title: str
    company: str
    url: str
    
class SearchResults(BaseModel):
    matches: list[JobSearchResult]
    total_found: int
    query_used: SearchQuery  # echo back for debugging
```

### Change 2: State now tracks search history

v1's state was just `messages`. v2 adds memory of what the agent has already tried, so it doesn't repeat itself or give up after one empty result.

```python
class JobScoutState(TypedDict):
    messages: Annotated[list, add_messages]
    search_history: list[SearchQuery]  # what's been tried
    fetched_urls: list[str]  # what's already been fetched
```

The `mock_search` function will need a small change to handle the structured input — search across keywords/location/role_type with OR logic across keywords (any match) and AND across fields (all fields must match).

**Wait — that means modifying shared/mock_jobs.py?** No. Create a v2-specific search adapter in `v2/search_adapter.py` that takes a `SearchQuery` and translates it into calls to the existing `mock_search(query: str)`. The shared mock data stays untouched.

### Change 3: Updated system prompt teaches the LLM how to decompose

The v1 system prompt was generic. v2's system prompt explains what each Pydantic field means and gives examples of decomposition.

---

## Files to create (all under `v2/`)

```
v2/
├── __init__.py             ← empty
├── README.md               ← what's in v2, how to run it (template below)
├── schemas.py              ← Pydantic models for tool inputs and outputs
├── state.py                ← JobScoutState with search_history
├── search_adapter.py       ← bridges structured SearchQuery to shared mock_search
├── tools.py                ← @tool functions with structured args/returns
├── agent.py                ← build_graph() with v2 system prompt
├── run.py                  ← CLI entry: python -m v2.run "query"
└── tests/
    ├── __init__.py         ← empty
    ├── tasks.py            ← reuses the same 10 tasks from v1 (import from v1)
    └── run_tasks.py        ← runs all 10, saves output for comparison
```

---

## File-by-file requirements

### `v2/__init__.py`

Empty file.

### `v2/schemas.py`

All Pydantic models live here. Single source of truth for v2's structured outputs.

```python
"""Pydantic schemas for JobScout v2 tool inputs and outputs.

The whole point of v2 is forcing the LLM to decompose user queries into
structured fields, instead of passing free-form sentences. These schemas
are the contract.
"""
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Structured query for searching jobs.
    
    The LLM fills this in from the user's natural-language request.
    Decomposing is the whole point — not passing the full sentence.
    """
    keywords: list[str] = Field(
        description="Job-related keywords to match against title and description. "
                    "E.g. ['Python', 'backend'] or ['ML', 'engineer']. "
                    "Pass single technical terms, not sentences."
    )
    location: str | None = Field(
        default=None,
        description="City or 'remote' to filter by. E.g. 'Seattle', 'Remote'. "
                    "None if user did not specify."
    )
    role_seniority: str | None = Field(
        default=None,
        description="Seniority level if specified. E.g. 'senior', 'junior', 'staff', 'principal'. "
                    "None if not specified."
    )


class FetchInput(BaseModel):
    """Structured input for fetching a single job description."""
    url: str = Field(description="The full URL of the job posting.")


class JobSearchResult(BaseModel):
    """A single job in search results — minimal info."""
    title: str
    company: str
    url: str


class SearchResults(BaseModel):
    """Result of a search_jobs call."""
    matches: list[JobSearchResult]
    total_found: int
    query_used: SearchQuery  # echo for debugging and the LLM's memory
```

### `v2/state.py`

```python
"""Agent state for JobScout v2.

Adds search_history and fetched_urls so the agent has explicit memory of
what it has tried — beyond just the message thread.
"""
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

from v2.schemas import SearchQuery


class JobScoutState(TypedDict):
    messages: Annotated[list, add_messages]
    search_history: list[SearchQuery]  # every search the agent has run
    fetched_urls: list[str]  # every URL the agent has fetched
```

### `v2/search_adapter.py`

The adapter that takes a structured `SearchQuery` and translates it into the existing `mock_search` calls. This lets v2 use structured input without modifying `shared/mock_jobs.py`.

```python
"""Bridges v2's structured SearchQuery to the v1-era mock_search function.

Strategy:
1. Run mock_search once per keyword (OR-style across keywords).
2. Deduplicate results by URL.
3. If location is specified, filter results by fetching descriptions
   and checking the location field.
4. If role_seniority is specified, filter by checking the title.

This avoids modifying shared/mock_jobs.py while still giving v2 structured
behavior. Note: in a real system, the search backend would natively support
structured queries — this adapter exists because we kept v1's tools intact.
"""
from shared.mock_jobs import mock_search, mock_fetch
from v2.schemas import SearchQuery, JobSearchResult, SearchResults


def structured_search(query: SearchQuery) -> SearchResults:
    """Run a structured search by combining single-keyword mock_search calls."""
    seen_urls = set()
    matches: list[JobSearchResult] = []

    # Step 1: Run one search per keyword, deduplicate
    for keyword in query.keywords:
        for r in mock_search(keyword):
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                matches.append(JobSearchResult(
                    title=r["title"],
                    company=r["company"],
                    url=r["url"],
                ))

    # Step 2: If location is specified, filter by fetching descriptions
    if query.location:
        loc_lower = query.location.lower()
        filtered = []
        for m in matches:
            desc = mock_fetch(m.url)
            if loc_lower in desc.lower():
                filtered.append(m)
        matches = filtered

    # Step 3: If seniority is specified, filter by title
    if query.role_seniority:
        sen_lower = query.role_seniority.lower()
        matches = [m for m in matches if sen_lower in m.title.lower()]

    # Step 4: Cap at 5 results, same as v1
    matches = matches[:5]

    return SearchResults(
        matches=matches,
        total_found=len(matches),
        query_used=query,
    )
```

### `v2/tools.py`

```python
"""Tools for JobScout v2 — structured inputs and outputs."""
from langchain_core.tools import tool
from shared.mock_jobs import mock_fetch
from v2.schemas import SearchQuery, FetchInput, SearchResults
from v2.search_adapter import structured_search


@tool
def search_jobs(query: SearchQuery) -> SearchResults:
    """Search for jobs using a structured query.

    Decompose the user's request into:
    - keywords: single technical terms (e.g. ['Python'], ['ML', 'engineer'])
    - location: city name or 'Remote', None if unspecified
    - role_seniority: 'senior', 'junior', 'staff', 'principal', None if unspecified

    Do NOT pass full sentences as keywords. Each keyword should be a single term.

    Returns matching jobs with title, company, and URL only.
    Call fetch_description for full details.
    """
    return structured_search(query)


@tool
def fetch_description(input: FetchInput) -> str:
    """Fetch the full job description for a single posting URL.

    Returns the description text including salary, remote status, and requirements.
    Call this after search_jobs when you need details that aren't in the search results.
    """
    return mock_fetch(input.url)
```

### `v2/agent.py`

The LangGraph wiring is similar to v1, but:
- Uses v2's state, schemas, tools
- Has an updated system prompt teaching decomposition
- Adds tracking of search_history and fetched_urls (in a custom node, since `ToolNode` doesn't update them automatically)

```python
"""JobScout v2 — single LangGraph agent with structured tool I/O and memory."""
import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from v2.state import JobScoutState
from v2.tools import search_jobs, fetch_description
from v2.schemas import SearchQuery

load_dotenv()

SYSTEM_PROMPT = """You are JobScout, an agent that helps users find jobs.

You have two tools:
- search_jobs: takes a STRUCTURED query (keywords, location, role_seniority)
- fetch_description: fetches full details for a single job URL

CRITICAL: when calling search_jobs, decompose the user's request:
- keywords: list of single technical terms (e.g. ['Python'], ['ML', 'engineer'])
- location: city name or 'Remote' (None if unspecified)
- role_seniority: 'senior', 'junior', 'staff', 'principal' (None if unspecified)

Do NOT pass full sentences as keywords. Each keyword is a single term.

Examples of good decomposition:
- "Find Python jobs in Seattle" → keywords=['Python'], location='Seattle'
- "Senior ML engineer roles, remote" → keywords=['ML', 'engineer'], location='Remote', role_seniority='senior'
- "Compare job_001 and job_003" → don't search, fetch each URL directly

If a search returns no results, try with fewer or different keywords before giving up.
If you've already tried a similar search, try a different decomposition rather than repeating.

Do not invent data you haven't seen in tool output.
"""


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
        has_system = any(getattr(m, "type", None) == "system" for m in messages)
        if not has_system:
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def tracking_node(state: JobScoutState):
        """Wrap ToolNode to also update search_history and fetched_urls."""
        # Run the tools
        tool_node = ToolNode(tools)
        result = tool_node.invoke(state)
        
        # Inspect the new messages to update memory
        new_history = list(state.get("search_history", []))
        new_fetched = list(state.get("fetched_urls", []))
        
        for msg in result.get("messages", []):
            if isinstance(msg, ToolMessage):
                # Check the original tool call to see what was invoked
                # Find the AIMessage immediately before this ToolMessage
                for prev in reversed(state["messages"]):
                    if hasattr(prev, "tool_calls") and prev.tool_calls:
                        for tc in prev.tool_calls:
                            if tc.get("id") == msg.tool_call_id:
                                if tc["name"] == "search_jobs":
                                    args = tc.get("args", {}).get("query", {})
                                    if args:
                                        try:
                                            new_history.append(SearchQuery(**args))
                                        except Exception:
                                            pass
                                elif tc["name"] == "fetch_description":
                                    args = tc.get("args", {}).get("input", {})
                                    url = args.get("url") if isinstance(args, dict) else None
                                    if url:
                                        new_fetched.append(url)
                        break
        
        return {
            "messages": result["messages"],
            "search_history": new_history,
            "fetched_urls": new_fetched,
        }

    graph = StateGraph(JobScoutState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tracking_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile()
```

### `v2/run.py`

```python
"""CLI entry point for running JobScout v2 against a single query."""
import sys
from v2.agent import build_graph


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m v2.run "your query here"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    graph = build_graph()
    result = graph.invoke(
        {
            "messages": [("user", query)],
            "search_history": [],
            "fetched_urls": [],
        },
        config={"recursion_limit": 10},
    )

    print("\n=== JobScout v2 result ===\n")
    print(result["messages"][-1].content)
    print(f"\n=== {len(result['messages'])} messages ===")
    print(f"=== {len(result.get('search_history', []))} searches ===")
    print(f"=== {len(result.get('fetched_urls', []))} fetches ===")


if __name__ == "__main__":
    main()
```

### `v2/tests/__init__.py`

Empty.

### `v2/tests/tasks.py`

**Reuse the v1 task list directly. Do not duplicate.**

```python
"""Reuses the same 10-task list from v1 so v2 results are directly comparable."""
from v1.tests.tasks import TASKS

__all__ = ["TASKS"]
```

### `v2/tests/run_tasks.py`

Same shape as v1's runner, but imports v2's graph:

```python
"""Run all 10 tasks against JobScout v2 and print results.

Identical structure to v1's runner so outputs can be diffed line-by-line.
"""
from v2.agent import build_graph
from v2.tests.tasks import TASKS


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
                {
                    "messages": [("user", task["query"])],
                    "search_history": [],
                    "fetched_urls": [],
                },
                config={"recursion_limit": 10},
            )
            answer = result["messages"][-1].content
            steps = len(result["messages"])
            n_searches = len(result.get("search_history", []))
            n_fetches = len(result.get("fetched_urls", []))
            print(f"\nAnswer:\n{answer}")
            print(f"\nMessages: {steps} | Searches: {n_searches} | Fetches: {n_fetches}")
            results.append({
                "task_id": task["id"],
                "steps": steps,
                "searches": n_searches,
                "fetches": n_fetches,
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

### `v2/README.md`

```markdown
# JobScout v2 — Structured Outputs and Memory

The same agent loop as v1, but the LLM now decomposes natural-language queries
into structured fields, and the state remembers what's already been tried.

**Companion post:** [P3: Structured outputs and memory](https://rajeshkartha.substack.com)

## What this version adds over v1

- Pydantic schemas for all tool inputs and outputs
- The LLM has to fill in `keywords`, `location`, `role_seniority` separately
- State tracks `search_history` and `fetched_urls`
- System prompt explicitly teaches decomposition with examples

## What it still doesn't have (yet)

- Multi-agent setup (v3)
- MCP integration (v4)
- Real APIs
- Observability or evals (v5)

## Run

From the `jobscout/` root:

```bash
poetry run python -m v2.run "Find me Python jobs in Seattle"
```

Run the 10-task test set:

```bash
poetry run python -m v2.tests.run_tasks
```

## Comparing v1 vs v2

The 10 tasks are identical. Results live in `eval/results/v1-run-001.txt`
and `eval/results/v2-run-001.txt`. Diff them to see exactly what changed.
```

---

## Acceptance criteria

After Cursor finishes, all of these must be true:

1. `shared/mock_jobs.py` is unchanged from v1
2. `v1/` is unchanged from v1
3. `poetry run python -m v2.run "Find me Python jobs in Seattle"` returns a sensible answer that references real mock data
4. The agent's tool calls show structured arguments (verifiable in a debug print of `result["messages"]`)
5. `result["search_history"]` and `result["fetched_urls"]` are populated after a multi-step run
6. `poetry run python -m v2.tests.run_tasks` runs all 10 tasks without crashing
7. The agent uses both `search_jobs` and `fetch_description` across the 10 tasks
8. The 10 tasks reuse the same task list as v1 (verifiable: `from v1.tests.tasks import TASKS` works)

---

## What NOT to build

- Multi-agent decomposition (planner/searcher/analyzer) — that's v3
- MCP servers — that's v4
- Real APIs — later
- Observability/Phoenix/DeepEval — v5
- Streaming — v7
- Async tool execution — not needed
- A web UI

---

## Style guide

Same as v1: type hints everywhere, docstrings on public functions and especially `@tool` docstrings, one file = one concept, no clever metaprogramming.

The new file is `search_adapter.py` — read that one carefully. It's where v2's structured input meets v1's flat-string mock data, and it's the part most likely to have subtle bugs.

---

## Suggested invocation

In Cursor's Claude Code chat:

> Read jobscout/v2/SPEC.md (this file). Build v2 exactly as specified.
>
> Phase 1: Create v2/schemas.py, v2/state.py, v2/search_adapter.py.
> Phase 2: Create v2/tools.py, v2/agent.py, v2/run.py.
> Phase 3: Create v2/tests/ files.
> Phase 4: Create v2/README.md.
>
> Do NOT modify v1/ or shared/. Do NOT add features that the spec excludes.
>
> After finishing, run `poetry run python -m v2.run "Find me Python jobs in Seattle"` and verify it returns a sensible answer (no API calls beyond what the run itself makes).

If Cursor wants to "improve" the search adapter or add features, point it back to "What NOT to build."