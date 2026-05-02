# JobScout v4 — MCP Integration with CareerTailor

v4 adds a fourth subgraph (`fit_analyzer`) that calls CareerTailor's MCP server
through the standard Model Context Protocol. When the user asks about resume-
to-job fit, the fit_analyzer enriches the answer with structured analysis from
CareerTailor.

> **Heads-up: v4 is the first version that requires real external setup.**
> v1 through v3 ran with mock data only — clone the repo, install dependencies,
> done. v4 calls a real service that depends on a real database and a real
> ingested resume. If you only want to read the code and see the demo output,
> the [v4 results](../eval/results/) folder has everything. To run v4 yourself,
> read the prerequisites below.

## What v4 adds over v3

- A new `fit_analyzer` subgraph in `v4/agents/fit_analyzer.py`
- An MCP client wrapper in `v4/mcp_client.py` (Streamable HTTP, 30s timeout)
- A new `analyze_fit_for: list[str]` field on `Plan` that the planner sets when
  the user asks for fit scoring
- A new `JobFitAnalysis` model representing one CareerTailor result per URL
- A conditional edge in the orchestrator that routes `analyzer → fit_analyzer`
  when `plan.analyze_fit_for` is non-empty

## Architecture

```
START -> planner -> [refusal? -> END]
                 -> searcher -> analyzer -> [fit needed? -> fit_analyzer] -> END
```

The fit_analyzer subgraph calls a separate process (CareerTailor's MCP server)
over HTTP. Two repos, two Poetry envs, one standardized protocol.

## Prerequisites

You'll need all of these to run v4 end-to-end:

1. **A working CareerTailor checkout.** v4 depends on
   [github.com/peeyar/careertailer](https://github.com/peeyar/careertailer)
   running locally. CareerTailor itself requires:
   - Python 3.11+, Poetry
   - A Supabase project with `resume_chunks` and `analysis_jobs` tables (SQL
     scripts are in CareerTailor's repo)
   - A Gemini API key
   - An ingested master resume — uploaded through CareerTailor's frontend or
     `/api/ingest` endpoint

2. **The CareerTailor MCP server running.** From CareerTailor's repo:
   ```bash
   cd careertailer/backend
   poetry run python -m app.mcp_server
   ```
   The server listens on `http://localhost:8765/mcp` by default. Leave it
   running in a dedicated terminal.

3. **JobScout v4 environment variables.** In `jobscout/.env`:
   ```
   GEMINI_API_KEY=...                  # JobScout's own Gemini key (same model)
   V4_DEFAULT_USER_ID=<uuid>           # The Supabase user_id whose master resume to use
   CAREERTAILER_MCP_URL=http://localhost:8765/mcp   # Optional, this is the default
   ```

4. **A second terminal for JobScout itself.** The MCP server stays running in
   terminal 1. JobScout v4 commands run in terminal 2.

If any of these aren't in place, v4 still runs — but the fit_analyzer will
either log a "server unreachable" error or skip silently (if
`V4_DEFAULT_USER_ID` isn't set). The rest of v4 (planner, searcher, analyzer)
behaves exactly like v3.

## Run

From `jobscout/`:

```bash
poetry run python -m v4.run "How well does my resume match the job at https://example.com/jobs/job_001?"
```

Run the 10-task formal eval:

```bash
poetry run python -m v4.tests.run_tasks
```

## What you should expect to see

On a working setup, a fit-analysis query produces output ending with:

```
=== Fit analyses: 1 ===
   https://example.com/jobs/job_001: 35/100
```

Real ranges and scores will vary — see `eval/results/v4-fit-demo-001.txt` for
three saved demo runs (single-URL, two-URL ranking, and a deliberately failed
three-URL parallel call that surfaces a known limitation).

## Graceful degradation

v4 is designed to never crash because of MCP issues:

- If the CareerTailor MCP server is unreachable, the fit_analyzer logs the
  error and returns the analyzer's answer unchanged.
- If `V4_DEFAULT_USER_ID` is not set, the fit_analyzer logs and skips.
- Individual MCP call failures (one URL out of three, etc.) are skipped per-URL
  so partial results still come through.

This is the production pattern: external services fail; agents that depend on
them shouldn't.

## Known limitations

- **Parallel MCP calls beyond 2 are unstable.** v4 opens a new MCP session per
  tool call. With 3+ parallel calls (e.g. ranking 3+ URLs), the Streamable HTTP
  transport's connection race can cause failures. Demo 3 in
  `eval/results/v4-fit-demo-001.txt` shows this. Future fix: session reuse
  across calls.
- **Match scores are not perfectly deterministic** even at `temperature=0`.
  Same job + same resume can produce different numeric scores across runs
  (the qualitative analysis stays consistent). Production fit-scoring needs
  calibration or design that doesn't rely on absolute numbers.
- **The 10-task formal eval doesn't exercise fit analysis.** None of the v1-era
  tasks ask for fit scoring, so v4's eval score is identical to v3's. v4's new
  capability is demonstrated through the fit-demo file, not the formal eval.
  P6 will rebuild the eval set to fix this.

## Companion post

[P5: MCP — wrapping CareerTailor (JobScout v4)](https://rajeshkartha.substack.com)
