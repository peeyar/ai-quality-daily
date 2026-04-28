"""Tools available to JobScout v1. Two of them — search and fetch."""
from langchain_core.tools import tool
from shared.mock_jobs import mock_search, mock_fetch


@tool
def search_jobs(query: str) -> list[dict]:
    """Search for jobs matching a natural-language query.

    Returns up to 5 results with title, company, and URL only. No salary,
    no description, no remote status — call fetch_description for those.

    Use this first when looking for jobs.
    """
    return mock_search(query)


@tool
def fetch_description(url: str) -> str:
    """Fetch the full job description for a single job posting URL.

    Returns the description text including salary, remote status, and
    requirements. Call this after search_jobs when you need details
    that aren't in the search results.
    """
    return mock_fetch(url)
