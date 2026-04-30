"""Pydantic schemas for JobScout v3.

v3 reuses v2's SearchQuery and FetchInput, but adds three new models that
are the contracts BETWEEN agents:
- Plan: what the planner produces
- SearcherResult: what the searcher produces
- FinalAnswer: what the analyzer produces
"""
from pydantic import BaseModel, Field


# Reused from v2 (recopied here so v3 is standalone)
class SearchQuery(BaseModel):
    keywords: list[str] = Field(
        description="Single technical terms, not sentences. E.g. ['Python']."
    )
    location: str | None = Field(
        default=None,
        description="City or 'Remote'. None if unspecified."
    )
    role_seniority: str | None = Field(
        default=None,
        description="'senior', 'junior', 'staff', etc. None if unspecified."
    )


class FetchInput(BaseModel):
    url: str = Field(description="The full URL of the job posting.")


class JobSearchResult(BaseModel):
    title: str
    company: str
    url: str


class SearchResults(BaseModel):
    matches: list[JobSearchResult]
    total_found: int
    query_used: SearchQuery


# New for v3 — the contracts between subgraphs

class PostFetchFilter(BaseModel):
    """A filter that requires the full job description to evaluate."""
    field: str = Field(
        description="What to check. E.g. 'salary_min', 'phd_required', 'remote'."
    )
    operator: str = Field(
        description="Comparison. E.g. '>=', '<=', '==', 'not_equal', 'contains'."
    )
    value: str | int | float | bool = Field(
        description="The value to compare against."
    )


class Plan(BaseModel):
    """What the planner produces. The searcher and analyzer execute against this."""
    user_intent: str = Field(
        description="One-sentence summary of what the user actually wants."
    )
    search_queries: list[SearchQuery] = Field(
        default_factory=list,
        description="Searches to run. Empty if the user gave URLs directly or "
                    "if no search makes sense for the request."
    )
    direct_fetches: list[str] = Field(
        default_factory=list,
        description="Job posting URLs to fetch directly, parsed from the user's request."
    )
    post_fetch_filters: list[PostFetchFilter] = Field(
        default_factory=list,
        description="Filters to apply after fetching descriptions. Used for things "
                    "the search tool can't filter on (salary, requirements, etc)."
    )
    refusal_reason: str | None = Field(
        default=None,
        description="Set if the request is impossible (e.g. 'I have no save tool'). "
                    "If set, searcher and analyzer are skipped."
    )
    answer_template: str = Field(
        description="How to format the final answer. E.g. 'Return the top 3 matches as a list.'"
    )


class SearcherResult(BaseModel):
    """What the searcher produces. The analyzer reads this."""
    search_hits: list[JobSearchResult] = Field(default_factory=list)
    fetched_descriptions: dict[str, str] = Field(
        default_factory=dict,
        description="URL -> full description text"
    )
    empty_queries: list[SearchQuery] = Field(
        default_factory=list,
        description="Queries that returned 0 results"
    )


class FinalAnswer(BaseModel):
    """What the analyzer produces. Goes back to the user."""
    answer: str
