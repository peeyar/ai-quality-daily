"""Run all 10 tasks against JobScout v4."""
from dotenv import load_dotenv
load_dotenv()

from v4.orchestrator import build_graph
from v4.tests.tasks import TASKS


def run_all():
    graph = build_graph()
    results = []

    for task in TASKS:
        print(f"\n{'='*70}")
        print(f"Task {task['id']} ({task['category']})")
        print(f"Query:    {task['query']}")
        print(f"Expected: {task['expected_behavior']}")
        print('='*70)

        try:
            result = graph.invoke({
                "user_query": task["query"],
                "plan": None,
                "searcher_result": None,
                "final_answer": None,
                "fit_analyses": [],
            })
            answer = result["final_answer"].answer
            plan = result["plan"]
            sr = result.get("searcher_result")
            n_fit = len(result.get("fit_analyses", []))
            print(f"\nAnswer:\n{answer}")
            print(f"\nPlan: {len(plan.search_queries)} searches, "
                  f"{len(plan.direct_fetches)} fetches, "
                  f"{len(plan.post_fetch_filters)} filters, "
                  f"{len(plan.analyze_fit_for)} fit-for")
            if sr:
                print(f"Searcher: {len(sr.search_hits)} hits, "
                      f"{len(sr.fetched_descriptions)} fetched, "
                      f"{len(sr.empty_queries)} empty queries")
            if n_fit:
                print(f"Fit analyses: {n_fit}")
            if plan.refusal_reason:
                print(f"REFUSED: {plan.refusal_reason}")
            results.append({
                "task_id": task["id"],
                "answer": answer,
                "refused": plan.refusal_reason is not None,
                "n_searches": len(plan.search_queries),
                "n_fetches": len(plan.direct_fetches) + (
                    len(sr.fetched_descriptions) if sr else 0
                ),
                "n_fit": n_fit,
                "error": None,
            })
        except Exception as e:
            print(f"\nERROR: {e}")
            results.append({"task_id": task["id"], "error": str(e)})

    return results


if __name__ == "__main__":
    results = run_all()
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    print(f"Total tasks: {len(results)}")
    print(f"Errored:     {sum(1 for r in results if r.get('error'))}")
    print(f"Completed:   {sum(1 for r in results if not r.get('error'))}")
    print(f"Refused:     {sum(1 for r in results if r.get('refused'))}")
    print(f"With fit:    {sum(1 for r in results if r.get('n_fit', 0) > 0)}")
    print("\nMark each task pass/fail manually based on the output above.")
