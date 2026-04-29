# JobScout

A job-search agent built in public, post by post, across 10 days.

This repo is the companion to the **AI Agents series** on [AI Quality Daily](https://rajeshkartha.substack.com). Each post adds one new capability to JobScout and one new metric to measure it. By the end, JobScout goes from a single LangGraph agent to a multi-agent system with MCP tools, A2A endpoints, observability, guardrails, and cost controls.

 **Note for early visitors:** This series ships post-by-post. Code lands in the  repo before each post publishes — so you may see versions ahead of the 
companion post. The roadmap table below shows the pairing.

## The series roadmap

| Day | Post | Folder | What's added |
|-----|------|--------|--------------|
| 1 | P1: Agent vs Workflow vs Chatbot | — | Definitions, no code |
| 2 | P2: Build your first JobScout | `v1/` | Single LangGraph agent, 2 tools, ReAct loop |
| 3 | P3: Structured outputs + memory | `v2/` | Pydantic schemas, short-term memory |
| 4 | P4: Multi-agent subgraphs | `v3/` | Planner + searcher + analyzer subgraphs |
| 5 | P5: MCP — wrap CareerTailor | `v4/` + `mcp-servers/` | MCP client, custom CareerTailor server |
| 6a | P6: Building the golden eval set | `eval/` | 20 tasks across 4 categories |
| 6b | P7: Observability + DeepEval | `v5/` | Phoenix tracing, DeepEval harness |
| 7 | P8: Expose via A2A | `a2a/` | Agent Card, A2A endpoint |
| 8 | P9: Reflection + retries | `v5/` updates | Reflection node, conditional retries |
| 9a | P10: Safety + guardrails | `v6/` | Direct + indirect prompt injection defense |
| 9b | P11: Fault tolerance | `v7/` | Circuit breakers, chaos testing |
| 10a | P12: Cost engineering | `v7/` updates | Token control, prompt compression, model routing |
| 10b | P13: The full picture | — | Wrap-up with charts |

## Quick start

```bash
cd jobscout
cp .env.example .env
# Add your GEMINI_API_KEY to .env
poetry install
```

Run any version:

```bash
poetry run python -m v1.run "Find me Python jobs in Seattle"
```

Run the test set for any version:

```bash
poetry run python -m v1.tests.run_tasks
```

## Project layout

```
jobscout/
├── pyproject.toml          # one Poetry project, all versions share deps
├── .env.example
├── shared/                 # code reused across versions
│   └── mock_jobs.py        # mock job postings, single source of truth
├── v1/                     # P2: single agent
├── v2/                     # P3: structured outputs + memory  (lands Day 3)
├── v3/                     # P4: multi-agent                  (lands Day 4)
├── v4/                     # P5: MCP                          (lands Day 5)
├── v5/                     # P7/P9: observability + reflection
├── v6/                     # P10: safety
├── v7/                     # P11/P12: fault tolerance + cost
├── mcp-servers/            # custom MCP servers (lands Day 5)
├── a2a/                    # A2A wrapper (lands Day 7)
└── eval/                   # golden set + run results (lands Day 6)
```

Each version folder is **standalone** — the code from v1 isn't a dependency of v2. This is deliberate: it lets readers clone any version and run it directly, and makes side-by-side diffs the teaching tool.

## Stack

- **Python** 3.11+
- **LangGraph** — orchestration
- **LangChain** — tool definitions, LLM bindings
- **Gemini 2.5 Flash** — the LLM (via `langchain-google-genai`)
- **Pydantic** v2 — schemas (from v2 onward)
- **MCP SDK** — Model Context Protocol (from v4 onward)
- **Arize Phoenix** + **DeepEval** — observability and evals (from v5 onward)

## Author

Rajesh Kartha — [rajeshkartha.substack.com](https://rajeshkartha.substack.com)
