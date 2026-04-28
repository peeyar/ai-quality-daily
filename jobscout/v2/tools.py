"""Tools for JobScout v2 — structured inputs and outputs."""
from langchain_core.tools import tool
from shared.mock_jobs import mock_fetch
from v2.schemas import SearchQuery, FetchInput, SearchResults
from v2.search_adapter import structured_search


@tool
def search_jobs(query: SearchQuery) -> SearchResults:
    """Search for jobs using a structured query.

    Decompose the user's request into:
    - keywords: single technical terms (e.g. ['Python'], ['ML', 'engineer'])
    - location: city name or 'Remote', None if unspecified
    - role_seniority: 'senior', 'junior', 'staff', 'principal', None if unspecified

    Do NOT pass full sentences as keywords. Each keyword should be a single term.

    Returns matching jobs with title, company, and URL only.
    Call fetch_description for full details.
    """
    return structured_search(query)


@tool
def fetch_description(input: FetchInput) -> str:
    """Fetch the full job description for a single posting URL.

    Returns the description text including salary, remote status, and requirements.
    Call this after search_jobs when you need details that aren't in the search results.
    """
    return mock_fetch(input.url)
