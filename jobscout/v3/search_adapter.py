"""Bridges v3's structured SearchQuery to the v1-era mock_search function.

Strategy:
1. Run mock_search once per keyword (OR-style across keywords).
2. Deduplicate results by URL.
3. If location is specified, filter results by fetching descriptions
   and checking the location field.
4. If role_seniority is specified, filter by checking the title.

This avoids modifying shared/mock_jobs.py while still giving v3 structured
behavior. Note: in a real system, the search backend would natively support
structured queries — this adapter exists because we kept v1's tools intact.
"""
from shared.mock_jobs import mock_search, mock_fetch
from v3.schemas import SearchQuery, JobSearchResult, SearchResults


def structured_search(query: SearchQuery) -> SearchResults:
    """Run a structured search by combining single-keyword mock_search calls."""
    seen_urls = set()
    matches: list[JobSearchResult] = []

    # Step 1: Run one search per keyword, deduplicate
    for keyword in query.keywords:
        for r in mock_search(keyword):
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                matches.append(JobSearchResult(
                    title=r["title"],
                    company=r["company"],
                    url=r["url"],
                ))

    # Step 2: If location is specified, filter by fetching descriptions
    if query.location:
        loc_lower = query.location.lower()
        filtered = []
        for m in matches:
            desc = mock_fetch(m.url)
            if loc_lower in desc.lower():
                filtered.append(m)
        matches = filtered

    # Step 3: If seniority is specified, filter by title
    if query.role_seniority:
        sen_lower = query.role_seniority.lower()
        matches = [m for m in matches if sen_lower in m.title.lower()]

    # Step 4: Cap at 5 results, same as v1
    matches = matches[:5]

    return SearchResults(
        matches=matches,
        total_found=len(matches),
        query_used=query,
    )
