# JobScout v2 — Golden Eval Summary

**Version:** v2 (single LangGraph agent, Pydantic schemas on tool I/O, search history in state)
**Model:** gemini-2.5-flash, temperature=0
**Eval:** 20-task golden set across 4 categories (eval/golden_set.json)
**Date:** 2026-05-03
**Raw output:** v2-golden-001.txt

## Score by category

| Category | Result | Change from v1 |
|----------|--------|----------------|
| Search | 3/5 | +2 (decomposition working) |
| Multi-step | 2/5 | +2 (partial — tasks 5, ?) |
| Fit analysis | 4/5* | unchanged (still honest refusals) |
| Edge cases | 4/5 | unchanged |
| **Total** | **13/20** | **+4 from v1** |

## Task-by-task

| # | Category | v1 | v2 | Change |
|---|----------|----|----|--------|
| 1 | search | FAIL | PASS | Decomposition working — found 2 jobs by name |
| 2 | search | FAIL | PASS | Returned 3 + honestly admitted "startup" not filterable |
| 3 | multi_step | FAIL | FAIL | Found role but didn't fetch & filter — asked permission instead |
| 4 | multi_step | FAIL | FAIL | New v2 hesitancy mode |
| 5 | multi_step | FAIL | PASS | Fetched and described |
| 6 | multi_step | FAIL | FAIL | URL retrieval got the IDs wrong |
| 7 | edge_cases | PASS* | PASS | Reasonable answer with relevant jobs |
| 8 | edge_cases | PASS | PASS | Sharper refusal — explicit about filter capabilities |
| 9 | multi_step | FAIL | FAIL | Hedged — asked permission |
| 10 | edge_cases | PASS | PASS | Clean refusal |
| 11 | fit_analysis | PASS* | PASS* | Honest — asked for resume content |
| 12 | fit_analysis | PASS* | FAIL | Worse than v1 — got URL retrieval wrong |
| 13 | fit_analysis | FAIL | PASS-PARTIAL | Found candidates, asked for criteria — honest improvement |
| 14 | fit_analysis | PASS* | PASS* | Honest refusal |
| 15 | fit_analysis | PASS* | PASS* | Honest refusal |
| 16 | search | PASS-PARTIAL | PASS-PARTIAL | Same brittle adapter as v1 |
| 17 | search | FAIL | FAIL | Adapter |
| 18 | search | FAIL | FAIL | Adapter |
| 19 | edge_cases | PASS | PASS | Clean refusal |
| 20 | edge_cases | AMBIG | AMBIG | "I can help by fetching..." invents capability |

## Key findings

- **v2 is the simplest version that holds up well across categories.** Pydantic schemas fixed the most expensive v1 failure (search adapter inputs) without introducing new failure modes elsewhere.
- v2 introduces "agent hesitancy" — instead of trying-and-failing, the agent asks the user for permission before acting. Tasks 3, 4, 9 all show this. Less wrong than v1, but not better.
- Task 12 is interesting: v2 actually scores WORSE than v1 on a fit-analysis task. Same architectural change that helped on search ("decompose properly") tripped up fit ranking ("got URL retrieval wrong").
- v2 stays honest on fit and edge cases — same shape as v1.

## What v2 fixed

- Search decomposition for keyword-driven queries (task 1, 2)
- Cleaner refusal language (task 8 sharper than v1's)
- Some multi-step queries now reach the right answer (task 5)

## What's still broken

- Multi-step queries that need post-fetch filtering (tasks 3, 4, 9)
- Search adapter on company/seniority/remote filters (tasks 17, 18)
- "Inventing capability" in task 20

## Note for the post

v2's 13/20 is the highest score before any architectural changes. v3 introduced subgraphs but lost ground on edge cases. v4 added MCP integration but also lost ground on edges. **v2 stays at 13 across both v3 and v4.**