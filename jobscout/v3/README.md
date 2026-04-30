# JobScout v3 — Multi-Agent with LangGraph Subgraphs

v3 splits the single agent from v2 into three specialized subgraphs:

- **Planner** decides what to attempt and how
- **Searcher** runs the structured queries and direct fetches
- **Analyzer** applies post-fetch filters and formats the answer

Each subgraph is decisive within its scope. The planner does NOT call tools.
The searcher does NOT decide what to filter. The analyzer does NOT decide
whether to attempt anything.

This architecture is meant to fix two failure modes from earlier versions:
1. v2's hesitancy on tasks 3, 4, 9 (the agent introspected on its tools and
   refused to attempt). The planner has no tools to introspect on — it just
   produces a plan.
2. v1's wrong-tool selection on task 6 (searched when it should have fetched).
   The planner explicitly distinguishes search_queries from direct_fetches.

**Companion post:** [P4: Multi-agent JobScout](https://rajeshkartha.substack.com)

## Run

From `jobscout/`:

```bash
poetry run python -m v3.run "Find me Python jobs in Seattle"
```

Run the full eval:

```bash
poetry run python -m v3.tests.run_tasks
```

## Architecture

```
START -> planner -> [refusal? -> END]
                 -> searcher -> analyzer -> END
```

Each agent is a compiled LangGraph in `v3/agents/`. The parent graph in
`v3/orchestrator.py` wires them together with one conditional edge.
