# JobScout v4 — Eval Run Summary

**Version:** v4 (multi-agent + MCP integration with CareerTailor)
**Model:** gemini-2.5-flash, temperature=0
**Tasks:** 10 (same as v1, see v1/tests/tasks.py) + 3 fit-demo queries (see below)
**Date:** 2026-05-02
**Raw output:** v4-run-001.txt (formal eval), v4-fit-demo-001.txt (demos)

## Formal eval results vs previous versions

| Task | Category | v1 | v2 | v3 | v4 | Notes |
|------|----------|----|----|----|----|----|
| 1 | simple | FAIL | PASS | PASS | PASS | No change |
| 2 | filtered | FAIL | PASS | PASS | PASS | No change |
| 3 | filtered_with_fetch | FAIL | FAIL | PASS | PASS | No change |
| 4 | filtered_with_fetch | FAIL | FAIL | FAIL | FAIL | Search adapter still brittle |
| 5 | fetch_then_search | PARTIAL | PASS | PASS | PASS | No change |
| 6 | multi_fetch | FAIL | FAIL | PASS | PASS | No change |
| 7 | vague | PASS | PASS | PASS | PASS | Nohange |
| 8 | missing_metadata | PASS | PASS | PASS* | PASS* | No change |
| 9 | multi_filter | FAIL | FAIL | FAIL | FAIL | Same root cause as task 4 |
| 10 | missing_tool | PASS | PASS | PASS | PASS | No change |

**Score: 8/10 — same as v3.**

## Why the score didn't move

The 10-task eval set was designed for v1's capabilities (search, filter, fetch). v4 added a NEW capability — resume-vs-job fit analysis through the CareerTailor MCP server. None of the 10 tasks ask for fit analysis, so the planner correctly set `analyze_fit_for=[]` for all of them.

The v4 architecture is fully working. The eval just doesn't measure what v4 added. The 3 fit-demo queries below show the new capability in action.

This is a deliberate choice: keep the 10-task eval frozen for clean v1→v4 comparison, and demonstrate v4's new capability separately. The proper expansion of the eval set lands in P6.

## Fit-demo queries (separate from formal eval)

3 ad-hoc queries to demonstrate the fit_analyzer + MCP integration:

### De Single URL fit analysis (PASS)
**Query:** "How well does my resume match the job at https://example.com/jobs/job_001?"

Plan: 0 searches, 1 fetch, 0 filters, 1 fit-for. Single MCP call to CareerTailor returned a structured analysis (15/100 score, with matching keywords on distributed systems and missing keywords on Python primary experience).

Architecturally clean: planner correctly set `analyze_fit_for`, fit_analyzer made one MCP call, CareerTailor's analyze_match ran end-to-end through Supabase + Gemini, structured response came back, analyzer enriched the answer.

### Demo 2 — Two URL ranking (PASS)
**Query:** "Rank these jobs by fit for me: job_001 and job_003"

Plan: 0 searches, 2 fetches, 0 filters, 2 fit-for. Two parallel MCP calls. Both returned with different scores (35/100 and 45/100), demonstrating that parallel MCP calls work for the 2-URL case.

### Demo 3 — Three URL ranking (FAILED — known limitation)
**Query:** "Which of these roles should I apply to: job_001, job_003, job_008?"

Plaearches, 3 fetches, 0 filters, 3 fit-for. The planner and searcher executed correctly. The fit_analyzer attempted 3 parallel MCP calls. **All three failed** with `ClosedResourceError` from anyio's connection pooling.

**Root cause:** v4's `mcp_client.py` opens a new MCP session per tool call. Three concurrent session initializations against the same server create a connection race that the Streamable HTTP transport doesn't reliably handle. Demo 1 (1 session) and demo 2 (2 parallel sessions) work; demo 3 (3 parallel sessions) hits the limit.

**Graceful degradation worked:** v4 caught the failures, logged them, and returned the analyzer's answer without fit data instead of crashing.

**Future fix:** session reuse — a single MCP session should handle multiple tool calls. Reserved for a later post (the v4 architecture is intentionally minimal).

## What v4 fixed

Nothing in the formal 10-task eval. Architecturally:

1. **Two production-grade systems talking through a standardized protocol.** JobScout v4 in o repo, CareerTailor MCP server in another, communicating via MCP over Streamable HTTP. Real subprocess, real network calls, real Supabase, real Gemini.
2. **Graceful degradation.** When the MCP server is unreachable (or any individual call fails), v4 returns the analyzer's answer with a logged warning. v4 never crashes because of MCP issues.
3. **A new subgraph (`fit_analyzer`)** that calls the MCP server in parallel using `asyncio.gather`. Demo 3 surfaced its limit.

## What's still broken

**Tasks 4 and 9** — same root cause as v3. Search adapter is brittle string matching. Replacing the search adapter itself with an MCP-style service is a candidate for a future post but not strictly part of v4's scope.

**Demo 3** — the 3-parallel-call connection race documented above.

## Hard-earned lessons from v4

1. The MCP SDK uses **camelCase** field names (`structuredContent` not `structured_content`). Spec was wrong. Caught at runtime.
2. **`load_dotenv()` must run BEFORE importing modules** that read env vat module level. v4's fit_analyzer reads `V4_DEFAULT_USER_ID` at import time; v3 didn't have this issue because nothing in v3 read env at module load.
3. **`temperature=0` is not perfectly deterministic** for free-form structured outputs. Demo 1 today returned 15/100; demo 2 (run within seconds) returned 35/100 for the same job_001. Production fit-scoring needs calibration or design that doesn't rely on absolute numbers.
4. **Per-call MCP sessions don't scale.** Parallel calls beyond 2-3 hit a connection race. Real MCP clients should reuse sessions across calls.

## What's next (P6 / v5)

The next post (P6) builds the proper golden eval set — 20 tasks across 4 categories, designed to actually measure agentic capabilities including fit analysis. v4's "the eval doesn't measure what we just added" gap motivates this directly.

P7 (v5) adds Phoenix observability and DeepEval automation against the new golden set.
