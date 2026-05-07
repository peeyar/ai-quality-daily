# JobScout v5 — v4 + Observability

v5 is structurally identical to v4 except for Phoenix instrumentation:

- `instrumentation.py` (new) — Phoenix setup, LangChain + MCP instrumentors
- `run.py` and `orchestrator.py` — call `register_phoenix()` before any graph builds
- All four subgraph files — wrapped node bodies in `with tracer.start_as_current_span(...)` blocks
- `mcp_client.py` — manual span around the MCP call so the cross-process boundary is visible

Everything else is intentionally a verbatim copy of v4. The point of v5 is
NOT new architecture; it's making v4 observable.

## What you see in Phoenix

When v5 runs against the golden eval, every task produces a trace tree like:

```
v5.orchestrator (root span)
├── v5.planner
│   └── ChatGoogleGenerativeAI.invoke (auto by LangChainInstrumentor)
├── v5.searcher
├── v5.analyzer
│   └── ChatGoogleGenerativeAI.invoke
└── v5.fit_analyzer
    ├── v5.fit_analyzer.mcp_call (per URL, parallel)
    │   └── MCP CallTool (auto by MCPInstrumentor)
    │       └── (cross-process) careertailer.analyze_job_fit
    │           └── google_genai.generate_content (auto)
    └── v5.fit_analyzer.mcp_call (parallel sibling)
        └── ...
```

The cross-process spans (CareerTailor side) join the trace because both processes
register with the same project name — `jobscout-v5` — at the same Phoenix endpoint.

## Running v5

Three terminals:

1. Phoenix server:
   ```
   pip install arize-phoenix  # if not already installed in your shell
   phoenix serve
   # opens http://localhost:6006
   ```

2. CareerTailor MCP server:
   ```
   cd careertailer/backend
   poetry run python -m app.mcp_server
   ```

3. JobScout v5:
   ```
   cd jobscout
   poetry run python -m v5.run "How well does my resume match the job at https://example.com/jobs/job_001?"
   ```

Visit http://localhost:6006 to see traces.

## Eval

Same golden eval set, run via the cross-version runner:

```
cd jobscout
poetry run python -m eval.run_golden --version v5
```

Each task produces a separate trace in Phoenix, viewable by query text or by trace ID.

## Companion post

[P6: Observability with Phoenix (JobScout v5)](https://rajeshkartha.substack.com)
