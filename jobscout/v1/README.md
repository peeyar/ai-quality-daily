# JobScout v1 — Single Agent

The simplest working agent: one LLM, two tools, ReAct loop.

**Companion post:** [P2: Build your first JobScout Agent](https://open.substack.com/pub/rajeshkartha/p/i-built-my-first-agent-in-80-lines?r=6rlhak&utm_campaign=post&utm_medium=web&showWelcomeOnShare=true)

## What this version has

- One LangGraph agent
- Two tools: `search_jobs`, `fetch_description`
- Mock data only — no real API calls
- ReAct loop with a 10-step recursion limit
- A 10-task informal test set

## What it doesn't have (yet)

- Pydantic schemas on outputs (v2)
- Memory beyond message history (v2)
- Multiple agents (v3)
- MCP integration (v4)
- Real APIs (v3+)
- Observability or evals (v5)

These are deliberate omissions — each one earns its own post in the series.

## Run

From the `jobscout/` root (one level up):

```bash
poetry run python -m v1.run "Find me Python jobs in Seattle"
```

Run the 10-task test set:

```bash
poetry run python -m v1.tests.run_tasks
```

## Files

- `agent.py` — graph wiring (build_graph)
- `state.py` — JobScoutState TypedDict
- `tools.py` — @tool wrappers around shared/mock_jobs
- `run.py` — CLI entry point
- `tests/tasks.py` — the 10-task list
- `tests/run_tasks.py` — runs all 10 and prints a summary

## Known limitations

v1 fails on tasks that need:
- Multiple filters applied at once (loses one)
- Vague queries (loops until recursion limit)
- Tools that don't exist (apologizes instead of refusing cleanly)

These are real failure modes, captured in the post and fixed across v2–v7.
