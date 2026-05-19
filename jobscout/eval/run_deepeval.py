"""Run DeepEval GEval scoring against existing golden results.

Reads .txt files from eval/results/golden/ (one per version), pairs each task's
output with its rubric, runs GEval, writes per-version JSON to eval/results/deepeval/.

Usage:
    poetry run python -m eval.run_deepeval --version v5
    poetry run python -m eval.run_deepeval --version all
"""
import argparse
import json
import re
from pathlib import Path

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from eval.deepeval_judge import get_judge
from eval.rubrics import TASK_RUBRICS

EVAL_DIR = Path(__file__).parent
GOLDEN_RESULTS_DIR = EVAL_DIR / "results" / "golden"
DEEPEVAL_RESULTS_DIR = EVAL_DIR / "results" / "deepeval"


def parse_results_file(path: Path) -> dict[str, dict]:
    """Parse a v{N}-golden-001.txt file into task_id -> {category, query, expected, answer}."""
    text = path.read_text()
    chunks = re.split(r"^={5,}\s*\n", text, flags=re.MULTILINE)
    tasks: dict[str, dict] = {}
    current_task_id: str | None = None
    current_task_data: dict | None = None

    for chunk in chunks:
        header_match = re.match(
            r"Task (\d+) \(([^)]+)\)\s*\nQuery:\s*(.+?)\nExpected:\s*(.+?)\s*$",
            chunk,
            re.DOTALL,
        )
        if header_match:
            task_num, category, query, expected = header_match.groups()
            current_task_id = f"task_{int(task_num):02d}"
            current_task_data = {
                "category": category.strip(),
                "query": query.strip(),
                "expected": expected.strip(),
                "answer": None,
            }
            tasks[current_task_id] = current_task_data
            continue

        if current_task_data is not None and chunk.lstrip().startswith("Answer:"):
            answer = chunk.split("Answer:", 1)[1].strip()
            current_task_data["answer"] = answer
            current_task_id = None
            current_task_data = None

    return tasks


def verdict_from_score(score: float) -> str:
    if score >= 0.7:
        return "PASS"
    if score >= 0.4:
        return "PARTIAL"
    return "FAIL"


def score_version(version: str, judge) -> dict:
    results_path = GOLDEN_RESULTS_DIR / f"{version}-golden-001.txt"
    if not results_path.exists():
        raise FileNotFoundError(f"Missing results file: {results_path}")

    tasks = parse_results_file(results_path)
    output = {"version": version, "tasks": {}}

    for task_id, task_data in tasks.items():
        if task_id not in TASK_RUBRICS:
            print(f"  Skipping {task_id} — no rubric defined")
            continue
        if not task_data.get("answer"):
            print(f"  Skipping {task_id} — no answer in results file")
            continue

        rubric = TASK_RUBRICS[task_id]
        test_case = LLMTestCase(
            input=task_data["query"],
            actual_output=task_data["answer"],
            expected_output=task_data["expected"],
        )
        metric = GEval(
            name=f"Task {task_id} correctness",
            criteria=rubric,
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.EXPECTED_OUTPUT,
            ],
            model=judge,
        )
        try:
            metric.measure(test_case)
            output["tasks"][task_id] = {
                "category": task_data["category"],
                "score": round(metric.score, 3),
                "reason": metric.reason,
                "verdict": verdict_from_score(metric.score),
            }
            print(
                f"  {task_id} ({task_data['category']}): "
                f"{metric.score:.2f} → {output['tasks'][task_id]['verdict']}"
            )
        except Exception as e:
            print(f"  {task_id} ERROR: {e}")
            output["tasks"][task_id] = {
                "category": task_data["category"],
                "error": str(e),
            }
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        choices=["v1", "v2", "v3", "v4", "v5", "all"],
        required=True,
    )
    args = parser.parse_args()

    DEEPEVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    judge = get_judge()
    versions = ["v1", "v2", "v3", "v4", "v5"] if args.version == "all" else [args.version]

    for version in versions:
        print(f"\n=== Scoring {version} ===")
        result = score_version(version, judge)
        output_path = DEEPEVAL_RESULTS_DIR / f"{version}-deepeval-001.json"
        output_path.write_text(json.dumps(result, indent=2))
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
