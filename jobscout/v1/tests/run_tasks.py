"""Run all 10 tasks against JobScout v1 and print results.

Pass/fail is currently manual — eyeball each result against the
expected behavior. Automated scoring lands in P6 with the golden eval set.
"""
from v1.agent import build_graph
from v1.tests.tasks import TASKS


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
                {"messages": [("user", task["query"])]},
                config={"recursion_limit": 10},
            )
            answer = result["messages"][-1].content
            steps = len(result["messages"])
            print(f"\nAnswer:\n{answer}")
            print(f"\nMessages: {steps}")
            results.append({
                "task_id": task["id"],
                "steps": steps,
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
