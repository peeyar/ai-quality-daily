# JobScout v1 — Eval Run Summary

**Version:** v1 (single agent, ReAct loop)
**Model:** gemini-2.5-flash, temperature=0
**Tasks:** 10 (see v1/tests/tasks.py)
**Date:** 2026-04-27
**Raw output:** v1-run-001.txt

## Results

| Task | Category | Pass/Fail | Notes |
|------|----------|-----------|-------|
| 1 | simple | FAIL | Found 0 results despite 4 Seattle Python jobs in mock data |
| 2 | filtered | FAIL | Found 0 ML engineer roles despite mock data containing them |
| 3 | filtered_with_fetch | FAIL | Did not call fetch_description |
| 4 | filtered_with_fetch | FAIL | Did not call fetch_description |
| 5 | fetch_then_search | PARTIAL | Fetched correctly, then search failed |
| 6 | multi_fetch | FAIL | Searched instead of fetching specific URLs |
| 7 | vague | PASS | Did not infinite-loop, gave up cleanly |
| 8 | missing_metadata | PASS | Refused cleanly, no hallucination |
| 9 | multi_filter | FAIL | Same query-decomposition failure as task 1 |
| 10 | missintool | PASS | Refused cleanly, no fake save |

**Score: 3 / 10**

## Root cause

Two failure modes account for 6 of the 7 failures:

1. **Query decomposition** — the agent passes the user's full sentence as the search query. Strict word matching means multi-word queries return [].
2. **Tool selection** — the agent searches when it should fetch (task 6).

Both are addressed in v2 (structured outputs force query decomposition) and v3 (planner agent owns tool selection).
