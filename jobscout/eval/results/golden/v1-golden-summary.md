# JobScout v1 — Golden Eval Summary

**Version:** v1 (single LangGraph agent, ReAct loop, 2 tools)
**Model:** gemini-2.5-flash, temperature=0
**Eval:** 20-task golden set across 4 categories (eval/golden_set.json)
**Date:** 2026-05-03
**Raw output:** v1-golden-001.txt

## Score by category

| Category | Result | Notes |
|----------|--------|-------|
| Search | 1/5 | Decomposition fails on most queries; only task 16 partial. |
| Multi-step | 0/5 | Cannot decompose multi-step queries; gives up immediately. |
| Fit analysis | 4/5* | Cannot do fit analysis but refuses honestly without inventing scores. |
| Edge cases | 4/5 | Honest refusals on save-to-file, company-size, HR-email, vague-query. |
| **Total** | **9/20** | |

\* Honest refusals counted as passes — v1 has no MCP integration and no resume access, so refusing to answer fit questions is correct behavior.

## Task-by-task

| # | Category | Outcome | Reason |
|---|----------|---------|--------|
| 1 | search | FAIL | Passed full natural-language query to string-matching search; got 0 hits. |
| 2 | search | FAIL | Same — no decomposition into "ML engineer" search keywords. |
| 3 | multi_step | FAIL | Couldn't decompose to search + post-fetch salary filter. |
| 4 | multi_step | FAIL | Same shape — couldn't separate "remote" search from "no PhD" filter. |
| 5 | multi_step | FAIL | Couldn't fetch the URL first, then search by similarity. |
| 6 | multi_step | FAIL | Searched instead of direct-fetching the two URLs. |
| 7 | edge_cases | PASS | Refused vague query honestly; didn't invent data. |
| 8 | edge_cases | PASS | Clean refusal on company-size filter ("not in tool data"). |
| 9 | multi_step | FAIL | Same root cause as task 4 — no multi-filter decomposition. |
| 10 | edge_cases | PASS | Clean refusal — no save tool exists. |
| 11 | fit_analysis | PASS* | Honest refusal: "my tools only allow me to search and fetch." |
| 12 | fit_analysis | PASS* | Honest — asked for clarification; didn't invent rankings. |
| 13 | fit_analysis | FAIL | Couldn't even find Seattle Python candidates to potentially fit. |
| 14 | fit_analysis | PASS* | Honest refusal on poor-fit explanation. |
| 15 | fit_analysis | PASS* | Honest refusal on threshold filter. |
| 16 | search | PASS-PARTIAL | Returned 1 of probably-several payment-related jobs. |
| 17 | search | FAIL | Couldn't decompose junior + frontend + remote. |
| 18 | search | FAIL | Couldn't filter by company name. |
| 19 | edge_cases | PASS | Clean refusal on HR contact info. |
| 20 | edge_cases | AMBIGUOUS | "I can help you tailor" invents capability v1 doesn't have. |

## Key findings

- v1's search adapter is the binding constraint — most failures trace back to passing full natural-language queries to a string-matching search tool.
- v1 holds up well on edge cases. Loop terminates cleanly; no infinite-tool-calling pathology.
- v1's fit-analysis "passes" are all honest refusals. v1 has no resume access. Counting these as passes is generous but defensible — v1 didn't lie or hallucinate scores.
- One ambiguous case (task 20) where v1 invents capability ("I can help you tailor your resume"). Not catastrophic but worth noting.

## What v1 fixed

Nothing. v1 is the baseline.

## What's still broken

- Search adapter brittleness (every search-category failure)
- Multi-step decomposition (every multi_step failure)
- Inventing capability on edge cases (task 20)