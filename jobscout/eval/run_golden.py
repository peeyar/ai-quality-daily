"""Cross-version runner for the golden eval set.

Loads eval/golden_set.json and runs all 20 tasks against each JobScout version
(v1-v5). Saves one results file per version under eval/results/golden/.

Usage from jobscout/ root:

    poetry run python -m eval.run_golden --version v1
    poetry run python -m eval.run_golden --version v2
    poetry run python -m eval.run_golden --version v3
    poetry run python -m eval.run_golden --version v4
    poetry run python -m eval.run_golden --version v5   # also requires Phoenix server
    poetry run python -m eval.run_golden --version all   # runs all five sequentially

Important: v4 and v5 require the CareerTailor MCP server to be running and the
V4_DEFAULT_USER_ID env var to be set. v5 additionally needs the Phoenix server
running on http://localhost:6006. If MCP is unavailable, fit_analysis tasks
will gracefully degrade (no scores) but the runner won't crash.
"""
import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env BEFORE importing version modules — v4's fit_analyzer reads env at module level.
load_dotenv()

# Each version's build_graph and the initial-state shape it expects.
# Same import pattern as each version's existing run.py.
VERSION_REGISTRY = {
    "v1": {
        "build": lambda: __import__("v1.agent", fromlist=["build_graph"]).build_graph(),
        "initial_state": lambda query: {"messages": [("user", query)]},
        "extract_answer": lambda result: result["messages"][-1].content,
    },
    "v2": {
        "build": lambda: __import__("v2.agent", fromlist=["build_graph"]).build_graph(),
        "initial_state": lambda query: {
            "messages": [("user", query)],
            "search_history": [],
            "fetched_urls": [],
        },
        "extract_answer": lambda result: result["messages"][-1].content,
    },
    "v3": {
        "build": lambda: __import__("v3.orchestrator", fromlist=["build_graph"]).build_graph(),
        "initial_state": lambda query: {
            "user_query": query,
            "plan": None,
            "searcher_result": None,
            "final_answer": None,
        },
        "extract_answer": lambda result: result["final_answer"].answer,
    },
    "v4": {
        "build": lambda: __import__("v4.orchestrator", fromlist=["build_graph"]).build_graph(),
        "initial_state": lambda query: {
            "user_query": query,
            "plan": None,
            "searcher_result": None,
            "final_answer": None,
            "fit_analyses": [],
        },
        "extract_answer": lambda result: result["final_answer"].answer,
    },
    "v5": {
        "build": lambda: __import__("v5.orchestrator", fromlist=["build_graph"]).build_graph(),
        "initial_state": lambda query: {
            "user_query": query,
            "plan": None,
            "searcher_result": None,
            "final_answer": None,
            "fit_analyses": [],
        },
        "extract_answer": lambda result: result["final_answer"].answer,
    },
}


def load_golden_set() -> dict:
    """Load the golden eval set from eval/golden_set.json."""
    path = Path(__file__).parent / "golden_set.json"
    with open(path) as f:
        return json.load(f)


def run_one_version(version: str, golden_set: dict) -> str:
    """Run all 20 tasks against the named version. Return formatted results."""
    if version not in VERSION_REGISTRY:
        raise ValueError(f"Unknown version: {version}")

    cfg = VERSION_REGISTRY[version]
    print(f"\n{'='*70}")
    print(f"Building {version} graph...")
    print('='*70)
    graph = cfg["build"]()

    output_lines = [f"# JobScout {version} — Golden Eval Run", ""]
    output_lines.append(f"Total tasks: {len(golden_set['tasks'])}")
    output_lines.append("")

    summary = {"errored": 0, "completed": 0, "by_category": {}}
    for cat in golden_set["categories"]:
        summary["by_category"][cat] = {"completed": 0, "errored": 0}

    for task in golden_set["tasks"]:
        header = f"\n{'='*70}\nTask {task['id']} ({task['category']})\nQuery:    {task['query']}\nExpected: {task['expected_behavior']}\n{'='*70}"
        print(header)
        output_lines.append(header)

        try:
            initial_state = cfg["initial_state"](task["query"])
            # Use generous recursion limit for v1/v2 ReAct loops; v3/v4 are bounded by their architecture.
            invoke_kwargs = {"config": {"recursion_limit": 15}} if version in ("v1", "v2") else {}
            result = graph.invoke(initial_state, **invoke_kwargs)
            answer = cfg["extract_answer"](result)
            print(f"\nAnswer:\n{answer}")
            output_lines.append(f"\nAnswer:\n{answer}\n")
            summary["completed"] += 1
            summary["by_category"][task["category"]]["completed"] += 1
        except Exception as e:
            err = f"\nERROR: {type(e).__name__}: {e}"
            print(err)
            output_lines.append(err)
            summary["errored"] += 1
            summary["by_category"][task["category"]]["errored"] += 1

    # Trailing summary
    summary_block = [
        "",
        "="*70,
        "SUMMARY",
        "="*70,
        f"Completed: {summary['completed']}/{len(golden_set['tasks'])}",
        f"Errored:   {summary['errored']}/{len(golden_set['tasks'])}",
        "",
        "By category:",
    ]
    for cat, counts in summary["by_category"].items():
        total_in_cat = sum(1 for t in golden_set["tasks"] if t["category"] == cat)
        summary_block.append(
            f"  {cat:<14} {counts['completed']}/{total_in_cat} completed"
            + (f" ({counts['errored']} errored)" if counts["errored"] else "")
        )
    summary_block.append("")
    summary_block.append("Mark each task pass/fail manually based on the output above.")
    summary_text = "\n".join(summary_block)
    print(summary_text)
    output_lines.append(summary_text)

    return "\n".join(output_lines)


def main():
    parser = argparse.ArgumentParser(description="Run the golden eval set against one or more JobScout versions.")
    parser.add_argument(
        "--version",
        choices=["v1", "v2", "v3", "v4", "v5", "all"],
        required=True,
        help="Which version to run. 'all' runs v1-v5 sequentially.",
    )
    args = parser.parse_args()

    golden_set = load_golden_set()
    versions = ["v1", "v2", "v3", "v4", "v5"] if args.version == "all" else [args.version]

    output_dir = Path(__file__).parent / "results" / "golden"
    output_dir.mkdir(parents=True, exist_ok=True)

    for version in versions:
        try:
            results = run_one_version(version, golden_set)
        except Exception as e:
            print(f"\n!! Failed to run {version}: {type(e).__name__}: {e}")
            continue

        out_path = output_dir / f"{version}-golden-001.txt"
        out_path.write_text(results)
        print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()
