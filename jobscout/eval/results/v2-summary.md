# JobScout v2 — Eval Run Summary

**Version:** v2 (single agent, Pydantic schemas, search/fetch memory)
**Model:** gemini-2.5-flash, temperature=0
**Tasks:** 10 (same as v1, see v1/tests/tasks.py)
**Date:** 2026-04-28
**Raw output:** v2-run-001.txt

## Results vs v1

| Task | Category | v1 | v2 | Notes |
|------|----------|----|----|-------|
| 1 | simple | FAIL | PASS | Found 2 Seattle Python jobs by name |
| 2 | filtered | FAIL | PASS | Returned 3 ML roles, honestly admitted can't filter "startup" |
| 3 | filtered_with_fetch | FAIL | FAIL* | New failure mode: asked permission instead of trying |
| 4 | filtered_with_fetch | FAIL | FAIL* | Same — hedged instead of attempting |
| 5 | fetch_then_search | PARTIAL | PASS | Fetched then searched, found similar role |
| 6 | multi_fetch | FAIL | FAIL | Attempted fetches (progress!) but used wrong URL format |
| 7 | vague | PASS | PASS | Answered with relevant AI jobs instead of giving up |
| 8 | missing_metadata | PASS SS | Refused with explicit reasoning about tools |
| 9 | multi_filter | FAIL | FAIL* | Hedged instead of attempting |
| 10 | missing_tool | PASS | PASS | Refused with explicit tool boundary |

*New failure mode: v2 became more cautious. Where v1 bashed search blindly,
v2 introspects on its capabilities and asks before trying.

**Score: 6/10 — up from v1's 3/10**

## What v2 fixed

1. Query decomposition — the headline win. Tasks 1, 2, 5, 7 now work because
   the LLM is forced to fill in keywords/location/seniority separately
   instead of passing full sentences.
2. Tool selection on task 6 — the agent now reaches for fetch when it should
   (still gets URL format wrong, but the right tool is chosen).

## What v2 introduced

A new failure mode: **agent hesitancy**. Tasks 3, 4, 9 used to fail because
the agent tried and got nothing. They now fail because the agent doesn't
even attempt — it asks for permission or surfaces tool limitations upfront.

This is a side effect of structured outputs: by makinent precise
about what it can do, we taught it to second-guess itself. A real-world
lesson — adding structure makes agents smarter AND more cautious.

## What's next (v3)

The hesitancy problem is fundamentally a single-agent problem. One LLM is
trying to plan, search, and decide whether to attempt — all in one head.

v3 splits these:
- A **planner** decides what to attempt (and isn't shy about trying)
- A **searcher** executes structured queries
- An **analyzer** post-filters results based on fetched descriptions

This should fix tasks 3, 4, 9 (planner attempts) and task 6 (analyzer
handles multi-fetch comparisons properly).
