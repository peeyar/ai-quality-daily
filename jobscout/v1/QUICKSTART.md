# Day 2 Quick Start — Building JobScout v1

Open the `ai-quality-daily/` folder in Cursor. Then walk this list top-to-bottom.

## 1. Verify the scaffold

You should see this layout:

```
ai-quality-daily/
├── README.md
├── .gitignore
├── careertailer/                   (your existing app, untouched)
└── jobscout/
    ├── README.md
    ├── pyproject.toml
    ├── .env.example
    ├── shared/
    │   ├── __init__.py
    │   └── mock_jobs.py            (stub — Cursor fills this)
    └── v1/
        ├── README.md
        ├── SPEC.md                 (the build spec for Cursor)
        └── (everything else gets created by Cursor)
```

If anything's missing, copy it from this scaffold before continuing.

## 2. Set up your environment

From the `jobscout/` folder:

```bash
cd jobscout
cp .env.example .env
```

Open `.env` and replace `your-gemini-api-key-here` with your real Gemini API key.

## 3. Open Cursor's Claude Code chat

Workspace should be `ai-quality-daily/` (the parent of `jobscout/`).

Paste this in:

> Read `jobscout/v1/SPEC.md`. Build the v1 application exactly as specified.
> First fill in `jobscout/shared/mock_jobs.py` with the mock data, then create
> all the files under `jobscout/v1/`. Do not touch anything outside `jobscout/`.
> After finishing, list what you created and what acceptance criteria you verified.

## 4. While Cursor works, watch for these traps

- **It tries to add Pydantic schemas in v1.** Stop it — that's v2.
- **It tries to call real APIs.** Stop it — mocks only in v1.
- **It "improves" the SPEC.** Tell it to follow the spec exactly. We want a deliberately minimal v1 so v2's improvements are visible.
- **It puts files in a nested `jobscout/v1/jobscout/` folder.** Tell it the package structure is flat — `v1/` is the package.

## 5. After Cursor finishes

```bash
cd jobscout
poetry install
poetry run python -m v1.run "Find me Python jobs in Seattle"
```

You should see a real answer that references the mock jobs. If not, the agent.py is broken — paste the error back into Cursor.

Then run the full test set:

```bash
poetry run python -m v1.tests.run_tasks
```

Watch all 10 tasks run. Eyeball each one against the "expected behavior" in `v1/tests/tasks.py`. Mark pass or fail on paper.

## 6. Update the P2 blog post with real numbers

Open `P2_jobscout_v1_single_agent.md`. Find this paragraph:

> Score: **6 out of 10 worked.** Tasks 1, 2, 4, 6 — clean. Task 3 — the agent invented salary numbers...

Replace **6 out of 10** with whatever your actual count was. Replace the per-task failure descriptions with what *actually* failed in your run. This is the most important edit — never publish placeholder numbers.

## 7. Commit and push

```bash
cd ai-quality-daily
git add jobscout/
git commit -m "P2: JobScout v1 — single agent, ReAct loop, 10-task test set"
git push
```

Make sure the GitHub repo is public before publishing P2.

## 8. Publish P2 on Substack

- Drop in the diagram PNG (we'll generate it before publish)
- Replace the placeholder pass/fail numbers with your real ones
- Final read-through for any unexplained shorthand
- Schedule for tomorrow morning, your usual posting time

## 9. (Optional but smart) Pre-build v2 and v3 tonight

If you have energy left after v1 works, ask Cursor to build v2 and v3 tonight using the same spec pattern. That gives you a 2-day buffer for the harder MCP day on Friday.

I'll write the v2 spec separately when you're ready.

---

## Time estimate

- Cursor builds v1: 15–30 minutes
- You verify and run the 10 tasks: 10 minutes
- Update the post with real numbers: 5 minutes
- Commit, push, publish: 10 minutes

**Total Day 2 effort after the scaffold: ~1 hour.**

That's the whole point of pre-scaffolding. The hard work was deciding the structure. Cursor does the typing.
