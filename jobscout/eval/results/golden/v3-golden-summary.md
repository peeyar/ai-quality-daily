# JobScout v3 — Golden Eval Summary

**Version:** v3 (multi-agent: planner/searcher/analyzer as separate compiled LangGraph subgraphs)
**Model:** gemini-2.5-flash, temperature=0
**Eval:** 20-task golden set across 4 categories (eval/golden_set.json)
**Date:** 2026-05-03
**Raw output:** v3-golden-001.txt

## Score by category

| Category | Result | Change from v2 |
|----------|--------|----------------|
| Search | 2/5 | -1 (regression on task 2) |
| Multi-step | 3/5 | +1 (signature win on tasks 3, 6) |
| Fit analysis | 3/5 | -1 (task 12 hallucinated) |
| Edge cases | 3/5 | -1 (task 8 regression, task 20 worse) |
| **Total** | **11/20** | **-2 from v2** |

## Task-by-task

| # | Category | v2 | v3 | Change |
|---|----------|----|----|--------|
| 1 | search | PASS | PASS | Same |
| 2 | search | PASS | **FAIL** | **Regression** — refused entirely instead of returning ML roles + caveat |
| 3 | multi_step | FAIL | PASS | Signature win — fetched, filtered, returned salary |
| 4 | multi_step | FAIL | FAIL | Searcher returned 0 |
| 5 | multi_step | PASS | PASS | Fetched and described |
| 6 | multi_step | FAIL | PASS | Big win — full structured comparison |
| 7 | edge_cases | PASS | PASS | Cautious but honest |
| 8 | edge_cases | PASS | **FAIL** | **Regression** — said "I cannot search without keywords" instead of refusing the size filter cleanly |
| 9 | multi_step | FAIL | FAIL | Searcher empty |
| 10 | edge_cases | PASS | PASS | Clean refusal |
| 11 | fit_analysis | PASS* | PASS* | Honest |
| 12 | fit_analysis | FAIL | **HALLUCINATION FAIL** | **Invented a ranking** — claimed job_003 better because of salary, job_001 "niche fit" because of PhD requirement. No resume to compare to. |
| 13 | fit_analysis | PASS-PARTIAL | FAIL | "Cannot identify best fit" — refused to even list candidates |
| 14 | fit_analysis | PASS* | PASS-PARTIAL | Described job, said "I cannot directly evaluate." |
| 15 | fit_analysis | PASS* | PASS* | Honest refusal |
| 16 | search | PASS-PARTIAL | PASS-PARTIAL | Same |
| 17 | search | FAIL | FAIL | Adapter |
| 18 | search | FAIL | FAIL | Adapter |
| 19 | edge_cases | PASS | PASS | Clean refusal |
| 20 | edge_cases | AMBIG | **HALLUCINATION FAIL** | **Worst response so far** — wrote actual resume update advice with specific Python years, distributed-systems wording. Made up advice based on the job description alone. |

## Key findings

- **v3 actually went DOWN on the golden set.** The original 10-task informal eval told a story of monotonic improvement (3 → 6 → 8). The new eval surfaces three regressions:
  1. Task 2 (3 ML engineer roles at startups): v2 returned 3 ML roles + said "can't filter startup". v3's planner saw "startup" as an unsupported filter and refused entirely. Hesitancy from v2 era moved to the planner level instead of the agent level. **The architectural fix didn't eliminate the failure mode — it relocated it.**
  2. Task 12 (rank by fit): v3 invented a ranking citing salary. That's pure hallucination. **The multi-agent architecture made it MORE confident in fabrication.**
  3. Task 20 (update my resume): v3 wrote detailed update advice for a resume it can't see. **More structure can mean more confident hallucination, not less.**
- v3's signature wins (tasks 3, 6) are real and meaningful. The planner/searcher/analyzer split unlocked fetch-and-filter and side-by-side comparison.
- v3 ties v1 on edge cases (3/5) but loses to v2 on every other dimension. The improvements on search/multi-step came at a cost.

## What v3 fixed

- Multi-step decomposition (tasks 3, 6 now work cleanly)
- Side-by-side comparison output

## What's still broken

- New: confident hallucination on edge-case fit-analysis tasks (12, 20)
- New: planner-level over-refusal (task 2 regression)
- Old: search adapter (17, 18)

## Note for the post

v3 is the version that hides regressions behind a single number. The 8/10 score on the informal eval looked like monotonic improvement; the golden set shows it isn't. This is the post's strongest finding.