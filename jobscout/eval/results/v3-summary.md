# JobScout v3 — Eval Run Summary

**Version:** v3 (multi-agent: planner + searcher + analyzer subgraphs)
**Model:** gemini-2.5-flash, temperature=0
**Tasks:** 10 (same as v1, see v1/tests/tasks.py)
**Date:** 2026-04-29
**Raw output:** v3-run-001.txt

## Results vs previous versions

| Task | Category | v1 | v2 | v3 | Notes |
|------|----------|----|----|----|-------|
| 1 | simple | FAIL | PASS | PASS | Found 2 Seattle Python jobs |
| 2 | filtered | FAIL | PASS | PASS | 3 ML roles, post-fetch filter applied |
| 3 | filtered_with_fetch | FAIL | FAIL | PASS | The signature v3 win — searched, fetched, filtered by salary, returned actual range |
| 4 | filtered_with_fetch | FAIL | FAIL | FAIL | Searcher returned 0 hits — search adapter limitation |
| 5 | fetch_then_search | PARTIAL | PASS | PASS | Planner correctly chose direct_fetches; analyzer read description |
| 6 | multi_fetch | FAILL | PASS | Direct fetches + structured comparison from descriptions |
| 7 | vague | PASS | PASS | PASS | Reasonable interpretation, returned relevant jobs |
| 8 | missing_metadata | PASS | PASS | PASS* | Refused via filter returning 0 — softer than v2's explicit "I can't filter by company size" |
| 9 | multi_filter | FAIL | FAIL | FAIL | Same root cause as task 4 — searcher returned 0 |
| 10 | missing_tool | PASS | PASS | PASS | Clean refusal via planner.refusal_reason |

**Score: 8/10 — up from v2's 6/10 and v1's 3/10**

## What v3 fixed

1. **Task 3 (the signature win)** — v2 hedged ("I can search but can't filter by salary"). v3's planner produces a plan that includes a post-fetch filter, the searcher fetches descriptions, the analyzer applies the filter. Three roles, decisive within scope.
2. **Task 6** — v1 and v2 both searched for "job_001" as a string and found nothing. v3's planner correctly identifies these as URLs and uses direct_fetches. Side-by-side comparison generated from real fetchtions.
3. **Task 5** — v1 returned half-credit (fetched correctly, search failed). v2 passed. v3's planner correctly identifies the URL reference, sets direct_fetches, and the analyzer reads the description to suggest similar roles.

## What's still broken

**Tasks 4 and 9.** Both fail with the same root cause: the search adapter does brittle substring matching against fields that don't exist as expected in the mock data. The planner produces correct plans. The analyzer would correctly filter if there were any hits. The searcher returns 0 hits because the tool layer is duct tape.

This is not a v3 architecture problem. It's a v2-era search adapter problem that v3 inherited verbatim.

**Task 8** — technically passes (no jobs returned for an impossible filter) but worse UX than v2 (which explicitly said "I can't filter by company size"). Minor.

## What's next (v4)

The remaining failures map cleanly to the next architectural step.

v4 wraps a real CareerTailor service as an MCP servJobScout calls it through the standard MCP protocol instead of through the brittle search adapter. The expectation: tasks 4 and 9 work because a real typed service handles "remote" and "PhD" as proper fields, not as substring matches in free text.

This is the senior-engineer pattern: when your tool layer is the bottleneck, swap it for a real protocol — don't rewrite duct tape.
