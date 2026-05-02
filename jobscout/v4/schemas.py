"""Pydantic schemas for JobScout v4.

v4 reuses v3's models and adds two things:
- a new `analyze_fit_for` field on Plan that triggers the fit_analyzer subgraph
- a new `JobFitAnalysis` model that the fit_analyzer produces (one per URL)
"""
from pydantic import BaseModel, Field


# Reused from v2/v3 (recopied here so v4 is standalone)
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


# Contracts between subgraphs (from v3)

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
    analyze_fit_for: list[str] = Field(
        default_factory=list,
        description=(
            "Job URLs that should get a CareerTailor fit analysis. Set this when "
            "the user wants to know how well their resume matches specific jobs, "
            "wants jobs ranked by fit, or wants advice on which roles to apply for. "
            "URLs in this list must also appear in direct_fetches OR be findable "
            "via search_queries — the system needs the full description text to "
            "send to CareerTailor."
        ),
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


class JobFitAnalysis(BaseModel):
    """Result of a single CareerTailor analyze_job_fit call."""
    url: str
    match_score: int
    matching_keywords: list[str]
    missing_keywords: list[str]
    summary_reasoning: str
