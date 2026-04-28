"""Pydantic schemas for JobScout v2 tool inputs and outputs.

The whole point of v2 is forcing the LLM to decompose user queries into
structured fields, instead of passing free-form sentences. These schemas
are the contract.
"""
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Structured query for searching jobs.

    The LLM fills this in from the user's natural-language request.
    Decomposing is the whole point — not passing the full sentence.
    """
    keywords: list[str] = Field(
        description="Job-related keywords to match against title and description. "
                    "E.g. ['Python', 'backend'] or ['ML', 'engineer']. "
                    "Pass single technical terms, not sentences."
    )
    location: str | None = Field(
        default=None,
        description="City or 'remote' to filter by. E.g. 'Seattle', 'Remote'. "
                    "None if user did not specify."
    )
    role_seniority: str | None = Field(
        default=None,
        description="Seniority level if specified. E.g. 'senior', 'junior', 'staff', 'principal'. "
                    "None if not specified."
    )


class FetchInput(BaseModel):
    """Structured input for fetching a single job description."""
    url: str = Field(description="The full URL of the job posting.")


class JobSearchResult(BaseModel):
    """A single job in search results — minimal info."""
    title: str
    company: str
    url: str


class SearchResults(BaseModel):
    """Result of a search_jobs call."""
    matches: list[JobSearchResult]
    total_found: int
    query_used: SearchQuery
