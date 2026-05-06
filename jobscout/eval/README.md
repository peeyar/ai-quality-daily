# JobScout Eval Set

The 20-task golden eval set used to grade JobScout v1-v4 (and future versions).

## Structure

20 tasks across 4 categories of 5 tasks each:

| Category | What it measures |
|----------|------------------|
| `search` | Basic search, filtering, retrieval. Single-tool calls. |
| `multi_step` | Multi-step reasoning, fetch-then-search, comparison, multi-filter. |
| `fit_analysis` | Resume-vs-job fit scoring through CareerTailor MCP (v4 capability). |
| `edge_cases` | Refusals, vague queries, out-of-scope requests. |

10 of the 20 tasks (IDs 1-10) carry over verbatim from `v1/tests/tasks.py` so
historical comparison stays meaningful. Tasks 11-20 are new — primarily fit
analysis (which v1-v3 cannot do) plus broader search and refusal cases the
informal v1 set didn't cover.

## Running

From the `jobscout/` root:

```bash
poetry run python -m eval.run_golden --version v1
poetry run python -m eval.run_golden --version v2
poetry run python -m eval.run_golden --version v3
poetry run python -m eval.run_golden --version v4    # requires CareerTailor MCP server
poetry run python -m eval.run_golden --version all   # runs v1-v4 sequentially
```

Each run produces a results file at `eval/results/golden/{version}-golden-001.txt`.

## Scoring

Manual pass/fail scoring against the `expected_behavior` field for each task.
P7 will introduce judge-LLM (DeepEval) scoring against the same set.

## Companion post

[P6: Building the golden eval set](https://rajeshkartha.substack.com)
