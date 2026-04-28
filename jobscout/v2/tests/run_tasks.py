"""Run all 10 tasks against JobScout v2 and print results.

Identical structure to v1's runner so outputs can be diffed line-by-line.
"""
from v2.agent import build_graph
from v2.tests.tasks import TASKS


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
            result = graph.invoke(
                {
                    "messages": [("user", task["query"])],
                    "search_history": [],
                    "fetched_urls": [],
                },
                config={"recursion_limit": 10},
            )
            answer = result["messages"][-1].content
            steps = len(result["messages"])
            n_searches = len(result.get("search_history", []))
            n_fetches = len(result.get("fetched_urls", []))
            print(f"\nAnswer:\n{answer}")
            print(f"\nMessages: {steps} | Searches: {n_searches} | Fetches: {n_fetches}")
            results.append({
                "task_id": task["id"],
                "steps": steps,
                "searches": n_searches,
                "fetches": n_fetches,
                "answer": answer,
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
    print("\nMark each task pass/fail manually based on the output above.")
