# JobScout v2 — Structured Outputs and Memory

The same agent loop as v1, but the LLM now decomposes natural-language queries
into structured fields, and the state remembers what's already been tried.

**Companion post:** [P3: Structured outputs and memory](https://open.substack.com/pub/rajeshkartha/p/pydantic-doubled-my-agents-pass-rate?r=6rlhak&utm_campaign=post&utm_medium=web&showWelcomeOnShare=true)

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
