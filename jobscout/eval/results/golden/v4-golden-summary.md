# JobScout v4 — Golden Eval Summary (post-fix)

**Version:** v4 (multi-agent + MCP integration with CareerTailor)
**Model:** gemini-2.5-flash, temperature=0
**Eval:** 20-task golden set across 4 categories (eval/golden_set.json)
**Date:** 2026-05-03 (initial run); 2026-05-03 (re-run after fit_analyzer fix)
**Raw output:** v4-golden-001.txt (post-fix, canonical)

## Score by category

| Category | Result | Change from v3 |
|----------|--------|----------------|
| Search | 2/5 | unchanged |
| Multi-step | 3/5 | unchanged |
| Fit analysis | 4/5 | +1 (real wins on 11, 12, 14, post-fix) |
| Edge cases | 4/5 | +1 (task 20 fixed post-fix) |
| **Total** | **13/20** | **+2 from v3, ties v2** |

## Task-by-task

| # | Category | v3 | v4 | Change |
|---|----------|----|----|--------|
| 1 | search | PASS | PASS | Same |
| 2 | search | FAIL | FAIL | Same — refused to attempt |
| 3 | multi_step | PASS | PASS | Same |
| 4 | multi_step | FAIL | FAIL | Adapter |
| 5 | multi_step | PASS | PASS | Same |
| 6 | multi_step | PASS | PASS | Same |
| 7 | edge_cases | PASS | PASS | Better — actually returned jobs |
| 8 | edge_cases | FAIL | FAIL | Same v3 regression |
| 9 | multi_step | FAIL | FAIL | Adapter |
| 10 | edge_cases | PASS | PASS | Clean refusal |
| 11 | fit_analysis | PASS* | **PASS** | **Headline win** — real 35/100 score with full structured matches/gaps |
| 12 | fit_analysis | HALLUCINATION FAIL | **PASS** | Real ranking with real scores: 35 vs 65. v3 invented; v4 measured. |
| 13 | fit_analysis | FAIL | PASS-PARTIAL | Honest refusal — search hits don't include descriptions, fit_analyzer can't run on URLs without descriptions. Architectural limit, not hallucination. |
| 14 | fit_analysis | PASS-PARTIAL | **PASS** | Surfaces missing keywords + reasoning ("AI/MLOps tools imply proficiency but not directly stated") |
| 15 | fit_analysis | PASS* | FAIL | "No jobs found matching your criteria" — pretends it tried the threshold filter. Documented architectural limit. |
| 16 | search | PASS-PARTIAL | PASS-PARTIAL | Same |
| 17 | search | FAIL | FAIL | Adapter |
| 18 | search | FAIL | FAIL | Adapter |
| 19 | edge_cases | PASS | PASS | Clean refusal |
| 20 | edge_cases | HALLUCINATION FAIL | PASS-with-caveat | **Fixed** — surfaces 15/100 score + improvement advice grounded in real missing_keywords |

## The bug found and fixed during P6

The first run of v4 against the golden set produced two contradictory outputs (tasks 14, 20):

> "While I couldn't perform a full resume analysis due to no resume being provided, here are the fit analyses from CareerTailor: 90/100. Matches: 'ML Engineer', 'Train models'..."

The "no resume provided" framing contradicted the real fit data displayed alongside it. **This was not honest refusal — the resume IS available; CareerTailor used it.**

### Root cause

The analyzer subgraph runs BEFORE the fit_analyzer and has no knowledge that fit data is coming. For resume-fit queries with no resume in the analyzer's immediate context, the analyzer faithfully follows its "do not invent data" instruction and writes "no resume was provided." The fit_analyzer then ran the MCP call (succeeded), got real scores, and tried to enrich the analyzer's wrong-framed answer — producing the contradiction.

### Fix

When fit_analyses are present, fit_analyzer now writes the user-facing answer from scratch using the structured fit data, instead of trying to enrich the analyzer's existing answer. The dependency on the upstream subgraph's framing is removed.

Specifically:
- `ENRICHMENT_PROMPT` renamed to `FIT_ANSWER_PROMPT` with explicit instruction not to claim "no resume was provided"
- `fit_analyzer_node` no longer reads `existing_answer.answer` when fit data exists; passes `plan.user_intent` and `plan.answer_template` directly
- Full keyword lists passed (was previously `[:3]` truncated)

### Impact

| Task | Pre-fix | Post-fix |
|------|---------|----------|
| 11 | PASS | PASS (fuller detail) |
| 12 | PASS | PASS (cleaner format) |
| 13 | FAIL | PASS-PARTIAL |
| 14 | HALLUCINATION FAIL | **PASS** |
| 20 | HALLUCINATION FAIL | **PASS-with-caveat** |

Net change: v4 fit_analysis category 2/5 → 4/5. v4 total 11/20 → 13/20.

## Key findings

- **v4 ties v2 at 13/20.** The architectural arc (single agent → schemas → multi-agent → MCP) didn't produce monotonic improvement on aggregate.
- v4 wins decisively on the fit_analysis category (4/5 vs v2's 4/5\* honest refusals). Where the architectural work was DESIGNED to win, it won. Where it wasn't (search, multi-step), v4 looks the same as v3.
- The golden eval did real work — it surfaced the fit_analyzer bug that v4's smoke test and the original 10-task informal eval missed. The fix turned a hallucination failure into a real win.
- **Task 13 is interesting architecturally.** v4 cannot do the compound query "search Seattle Python jobs → fit-analyze each one" because the planner produces search_queries (which return URL+title only) and the fit_analyzer needs full descriptions. The chain "search → fetch hits → fit analyze hits" requires either: a planner that does multi-step fetches, or a searcher that auto-fetches when fit is requested, or a fit_analyzer that can trigger fetches. None exist in v4. Real architectural limit; motivates a future post.

## What v4 fixed

- Real fit analysis on direct-URL queries (tasks 11, 12)
- Honest treatment of "why poor fit" with structured CareerTailor data (task 14 post-fix)
- "Update my resume" reinterpreted as "tell me what would improve fit" — uses real missing_keywords (task 20 post-fix)

## What's still broken

- Compound search-then-fit queries (task 13 — architectural)
- Threshold filtering on fit scores (task 15 — architectural)
- Same v3-era issues: search adapter (17, 18), planner over-refusal on task 2

## Note for the post

v4 finally lights up the fit category, but the more interesting finding is the bug-and-fix story. The eval caught real production-grade hallucination that informal eyeballing missed. **That's the eval doing real work** — not just "showing v4 wins." It also caught a real bug we then fixed.