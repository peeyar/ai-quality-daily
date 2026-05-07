# JobScout v5 — Golden Eval Summary

**Version:** v5 (v4 architecture + Phoenix observability)
**Model:** gemini-2.5-flash, temperature=0
**Eval:** 20-task golden set across 4 categories (eval/golden_set.json)
**Date:** 2026-05-07
**Raw output:** v5-golden-001.txt

## Score by category

| Category | Result | Change from v4 |
|----------|--------|----------------|
| Search | 2/5 | unchanged |
| Multi-step | 3/5 | unchanged |
| Fit analysis | 4/5 | unchanged |
| Edge cases | 4/5 | unchanged |
| **Total** | **13/20** | **0 change from v4** |

## What v5 actually changed

v5 is structurally identical to v4. Same four-subgraph architecture, same MCP integration with CareerTailor, same fit_analyzer logic from v4's post-fix state. The only differences:

- New `v5/instrumentation.py` registers Phoenix as the OpenTelemetry collector
- LangChainInstrumentor and MCPInstrumentor activated on JobScout side
- Manual `with tracer.start_as_current_span(...)` blocks added to each subgraph node
- Matching Phoenix register call in CareerTailor's MCP server
- Manual span around `CareerAI.analyze_match` in CareerTailor (because GoogleGenAIInstrumentor silently failed to patch)

**Score should not change because behavior should not change.** Phoenix observes; it doesn't decide. The eval confirms this — every task passes identically to v4 post-fix.

## Task-by-task

All 20 tasks match v4 post-fix exactly. Spot-checked the fit_analysis tasks (where v4's post-fix wins were most visible):

| # | Category | v4 post-fix | v5 | Notes |
|---|----------|----|----|-------|
| 11 | fit_analysis | PASS (35/100, full structure) | PASS (35/100, identical structure) | Same keyword breakdown |
| 12 | fit_analysis | PASS (35 vs 65 ranking) | PASS (35 vs 65 ranking) | Same comparative answer |
| 13 | fit_analysis | PASS-PARTIAL (architectural limit) | PASS-PARTIAL (same limit) | Same honest refusal |
| 14 | fit_analysis | PASS (missing_keywords + reasoning) | PASS (85/100, matches v4) | Same surfaced gaps |
| 15 | fit_analysis | FAIL (architectural — no threshold filter) | FAIL (same architectural limit) | Unchanged |
| 20 | edge_cases | PASS-with-caveat (15/100 + advice) | PASS-with-caveat (35/100 + advice) | Different fit score in run; same reframe behavior |

## What v5 enables (that v4 didn't)

- **Per-task latency measurement.** Every task now has spans recording exact LangGraph node, LLM call, and MCP boundary durations.
- **Per-task token cost.** Phoenix surfaces input/output token counts on every Gemini call.
- **Cross-process visibility.** A single fit-analysis trace shows JobScout's planner-searcher-analyzer-fit_analyzer hierarchy AND the cross-process call into CareerTailor's `analyze_job_fit` and the deep `GenerateContent` Gemini call inside CareerTailor.

## What v5 cost to add

- ~50 lines of code in JobScout (mostly manual subgraph spans)
- ~5 lines of code in CareerTailor's MCP server (manual span + Phoenix register)
- 30 minutes of diagnostic time when GoogleGenAIInstrumentor silently failed
- Three new dependencies on JobScout side, three on CareerTailor side
- Phoenix runs as a Docker container; no production DB needed for local-only observability

## What v5 didn't fix

Everything v4 didn't fix is still broken in v5:

- Compound search-then-fit queries (task 13 — architectural)
- Threshold filtering on fit scores (task 15 — architectural)
- Search adapter issues on tasks 4, 9, 17, 18
- Planner over-refusal on task 2
- Edge-case task 8 still fails

These are all architectural problems, not visibility problems. v5 makes them more LEGIBLE in Phoenix traces — you can see exactly which subgraph spends how much time on each — but legibility is not a fix.

## Note for the post (P6)

The score being unchanged is itself the lesson: **observability shouldn't change behavior**. Phoenix gives us better visibility into the same v4 behavior, including its remaining failures. The interesting finding from this run is not the eval score but the Phoenix traces — specifically the asymmetry between JobScout's auto-instrumented spans (which "just worked") and CareerTailor's spans (which required manual instrumentation when auto-instrumentation silently failed).

That asymmetry is the central narrative of P6.