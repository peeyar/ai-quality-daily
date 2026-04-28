"""
Mock job postings used by all versions of JobScout.

This is the single source of truth for test data — every version (v1, v2, v3, ...)
imports from here so that test results across versions are directly comparable.

The split between mock_search (title/company/url only) and mock_fetch (full
record) is deliberate: it forces the agent to actually use both tools instead
of one-shotting from search results.
"""

MOCK_JOBS: list[dict] = [
    {
        "url": "https://example.com/jobs/job_001",
        "title": "Senior Python Engineer",
        "company": "Acme Corp",
        "location": "Seattle, WA",
        "remote": "hybrid",
        "salary": "$180,000 - $220,000",
        "description": (
            "Senior Python Engineer to build large-scale data services. "
            "Requires 6+ years Python, distributed systems, and a PhD or "
            "equivalent research experience. Hybrid in Seattle, 3 days a week."
        ),
    },
    {
        "url": "https://example.com/jobs/job_002",
        "title": "ML Engineer",
        "company": "Tinybird Labs",
        "location": "San Francisco, CA",
        "remote": "remote",
        "salary": "$170,000 - $210,000",
        "description": (
            "Early-stage startup hiring our 4th ML engineer. Train and ship "
            "models end to end. No PhD required — we care about shipped work. "
            "Fully remote within the US."
        ),
    },
    {
        "url": "https://example.com/jobs/job_003",
        "title": "Senior Backend Engineer",
        "company": "MegaScale Systems",
        "location": "New York, NY",
        "remote": "hybrid",
        "salary": "$210,000 - $260,000",
        "description": (
            "Senior backend engineer on the payments platform. Go and Python, "
            "high-throughput services, on-call rotation. Hybrid in NYC."
        ),
    },
    {
        "url": "https://example.com/jobs/job_004",
        "title": "Data Scientist",
        "company": "Globex",
        "location": "Seattle, WA",
        # salary deliberately missing
        # remote deliberately missing
        "description": (
            "Data scientist on the forecasting team. PhD in statistics, "
            "economics, or related field strongly preferred. Seattle office."
        ),
    },
    {
        "url": "https://example.com/jobs/job_005",
        "title": "Frontend Engineer",
        "company": "Pixel & Ampersand",
        "location": "Remote",
        "remote": "remote",
        "salary": "$140,000 - $170,000",
        "description": (
            "Frontend engineer on a small design-tools team. React, "
            "TypeScript, a real eye for typography. Fully remote."
        ),
    },
    {
        "url": "https://example.com/jobs/job_006",
        "title": "DevOps Engineer",
        "company": "Cloudwave",
        "location": "San Francisco, CA",
        # remote deliberately missing
        "salary": "$160,000 - $190,000",
        "description": (
            "DevOps engineer owning Kubernetes, Terraform, and CI. SF office, "
            "in-person culture. No remote info listed."
        ),
    },
    {
        "url": "https://example.com/jobs/job_007",
        "title": "Senior ML Engineer",
        "company": "Foom",
        "location": "New York, NY",
        "remote": "hybrid",
        "salary": "$190,000 - $230,000",
        "description": (
            "Series A startup hiring senior ML engineers. LLM fine-tuning, "
            "evals, and inference infrastructure. No PhD required. Hybrid NYC."
        ),
    },
    {
        "url": "https://example.com/jobs/job_008",
        "title": "Python Backend Developer",
        "company": "Initech",
        "location": "Seattle, WA",
        "remote": "remote",
        "salary": "$150,000 - $180,000",
        "description": (
            "Python backend developer on internal tooling. Django, Postgres, "
            "REST APIs. Remote-first, occasional Seattle visits."
        ),
    },
    {
        "url": "https://example.com/jobs/job_009",
        "title": "Staff Backend Engineer",
        "company": "Vortex",
        "location": "Remote",
        "remote": "remote",
        "salary": "$230,000 - $280,000",
        "description": (
            "Staff-level backend engineer leading the API platform. 10+ years "
            "experience, distributed systems depth, mentorship. Fully remote."
        ),
    },
    {
        "url": "https://example.com/jobs/job_010",
        "title": "Junior Data Scientist",
        "company": "!! Hyphae !!",
        "location": "San Francisco, CA",
        "remote": "hybrid",
        # salary deliberately missing
        "description": (
            "Junior data scientist at a weirdly-named biotech. SQL, Python, "
            "and a willingness to learn. Salary not listed publicly."
        ),
    },
    {
        "url": "https://example.com/jobs/job_011",
        "title": "Senior Frontend Engineer",
        "company": "Beam",
        "location": "New York, NY",
        "remote": "remote",
        "salary": "$180,000 - $210,000",
        "description": (
            "Senior frontend engineer on the editor surface. React, "
            "performance work, design-system stewardship. Remote within US."
        ),
    },
    {
        "url": "https://example.com/jobs/job_012",
        "title": "DevOps / SRE",
        "company": "GreyMatter",
        "location": "Seattle, WA",
        # remote deliberately missing
        "salary": "$160,000 - $200,000",
        "description": (
            "Small startup, ~20 people. Own the SRE function end to end. "
            "Seattle preferred, remote info not specified."
        ),
    },
    {
        "url": "https://example.com/jobs/job_013",
        "title": "Principal ML Engineer",
        "company": "Quantitative Synthesis",
        "location": "San Francisco, CA",
        "remote": "hybrid",
        "salary": "$250,000 - $300,000",
        "description": (
            "Principal ML engineer on the trading research team. PhD in ML, "
            "statistics, or physics required. Hybrid SF."
        ),
    },
    {
        "url": "https://example.com/jobs/job_014",
        "title": "Python Data Engineer",
        "company": "the company formerly known as Foo",
        "location": "Remote",
        "remote": "remote",
        "salary": "$170,000 - $200,000",
        "description": (
            "Python data engineer on the analytics platform. Airflow, dbt, "
            "Snowflake. No PhD required. Fully remote."
        ),
    },
    {
        "url": "https://example.com/jobs/job_015",
        "title": "Senior ML Engineer",
        "company": "Nimbus",
        "location": "Austin, TX",
        "remote": "hybrid",
        # salary deliberately missing
        "description": (
            "Senior ML engineer at a 30-person startup. Recommendations and "
            "ranking. No PhD required. Hybrid in Austin."
        ),
    },
]


def mock_search(query: str) -> list[dict]:
    """Return up to 5 jobs matching the query. Returns only {title, company, url}.

    The agent must call mock_fetch to get details like salary and remote status.
    This forces real tool-use behavior.
    """
    q = query.lower()
    matches = []
    for job in MOCK_JOBS:
        haystack = " ".join(
            [
                job.get("title", ""),
                job.get("location", ""),
                job.get("description", ""),
            ]
        ).lower()
        if q in haystack:
            matches.append(
                {
                    "title": job["title"],
                    "company": job["company"],
                    "url": job["url"],
                }
            )
        if len(matches) == 5:
            break
    return matches


def mock_fetch(url: str) -> str:
    """Return the full description for a given URL, or a 'not found' string."""
    for job in MOCK_JOBS:
        if job["url"] == url:
            lines = [
                f"Title: {job['title']}",
                f"Company: {job['company']}",
                f"Location: {job.get('location', 'Not specified')}",
                f"Remote: {job.get('remote', 'Not specified')}",
                f"Salary: {job.get('salary', 'Not specified')}",
                "",
                "Description:",
                job.get("description", ""),
            ]
            return "\n".join(lines)
    return f"Job not found for URL: {url}"
