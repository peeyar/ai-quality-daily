"""The 10-task informal test set for JobScout v1.

These are deliberately mixed: simple cases JobScout should handle cleanly,
filtered cases that need fetch calls, vague queries that test the loop's
exit conditions, and impossible cases (missing tools or missing data).

Reused across v1, v2, v3 to allow direct comparison.
"""

TASKS = [
    {
        "id": 1,
        "query": "Find me Python jobs in Seattle",
        "category": "simple",
        "expected_behavior": "single search, return list",
    },
    {
        "id": 2,
        "query": "Find me 3 ML engineer roles at startups",
        "category": "filtered",
        "expected_behavior": "search then filter to 3 results",
    },
    {
        "id": 3,
        "query": "Senior backend roles paying over $200k",
        "category": "filtered_with_fetch",
        "expected_behavior": "search, fetch descriptions, filter by salary",
    },
    {
        "id": 4,
        "query": "Remote roles, no PhD required",
        "category": "filtered_with_fetch",
        "expected_behavior": "search, fetch, read requirements",
    },
    {
        "id": 5,
        "query": "Find me roles like the one at https://example.com/jobs/job_001",
        "category": "fetch_then_search",
        "expected_behavior": "fetch first, then search by similarity",
    },
    {
        "id": 6,
        "query": "Compare these two listings: job_001 and job_003",
        "category": "multi_fetch",
        "expected_behavior": "two fetches, structured comparison",
    },
    {
        "id": 7,
        "query": "What's hot in AI hiring this week?",
        "category": "vague",
        "expected_behavior": "should ask for clarification or interpret reasonably without infinite loop",
    },
    {
        "id": 8,
        "query": "Find me jobs but only at companies under 50 people",
        "category": "missing_metadata",
        "expected_behavior": "should admit company size is not in tool data",
    },
    {
        "id": 9,
        "query": "Senior MLE under $180k that don't require a PhD",
        "category": "multi_filter",
        "expected_behavior": "search, fetch, apply 3 filters at once",
    },
    {
        "id": 10,
        "query": "Save my top 3 to a file",
        "category": "missing_tool",
        "expected_behavior": "should refuse cleanly, no save tool exists",
    },
]
