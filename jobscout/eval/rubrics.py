"""GEval rubrics for the 20 golden tasks.

Each rubric is a string passed to DeepEval's GEval judge as evaluation criteria.
Rubrics are category-aware. Each rubric is honest about partial credit and
architectural limits so the judge can rate "honest refusals" appropriately
rather than failing them as wrong answers.

Rubrics have been refined to align with the `expected_behavior` text in
golden_set.json. For fit_analysis tasks (11-15) the rubric reflects both the
v4/v5 ideal behavior and the v1-v3 acceptable best-effort, because the same
rubric is applied across all versions.

Keep rubrics behavioral: what the output should DO, not what it should SAY.
"""

TASK_RUBRICS = {
    # ===== SEARCH (5 tasks) =====
    "task_01": (
        "Query: 'Find me Python jobs in Seattle'. Expected behavior: search by "
        "Python keyword + Seattle location and return matching jobs with title, "
        "company, and URL. In the mock data, job_001 (Senior Python Engineer at "
        "Rajesh Corp) and job_008 (Python Backend Developer at Initech) are the "
        "canonical matches. PASS if at least one matching Seattle Python job is "
        "listed with title and company (URL preferred). PARTIAL if jobs are "
        "listed but missing required fields, or only loosely match. FAIL if no "
        "jobs are returned or the jobs are unrelated/hallucinated."
    ),
    "task_02": (
        "Query: 'Find me 3 ML engineer roles at startups'. Expected behavior: "
        "search ML/engineer keywords, return up to 3 results, and acknowledge "
        "that the 'startup' filter is not natively supported. PASS if up to 3 "
        "relevant ML engineer roles appear AND the agent either acknowledges the "
        "startup-filter limitation or returns best-effort matches. PARTIAL if "
        "fewer than 3 roles are returned without explanation, or the startup "
        "caveat is missing. FAIL if the agent refuses without explanation or "
        "hallucinates a startup filter that does not exist."
    ),
    "task_16": (
        "Query: 'Show me 5 jobs in payments'. Expected behavior: search the "
        "'payments' keyword and return up to 5 job results with title, company, "
        "and URL. PASS if up to 5 payments-related jobs are listed with title "
        "and company. PARTIAL if fewer relevant jobs are returned, or required "
        "fields are missing. FAIL on hallucination or empty results when "
        "payments jobs exist in the mock data."
    ),
    "task_17": (
        "Query: 'Junior frontend roles, remote only'. Expected behavior: search "
        "frontend with junior seniority + remote filter and return matching "
        "roles. PASS if junior-level remote frontend roles are listed. PARTIAL "
        "if only some filters are applied (e.g., remote frontend but not "
        "junior). FAIL if the search returns empty despite qualifying jobs "
        "existing in mock data, or if results are unrelated."
    ),
    "task_18": (
        "Query: 'Jobs at Initech'. Expected behavior: filter jobs by company "
        "and return all Initech roles with title and URL. PASS if Initech's "
        "jobs are returned with title (URL preferred). PARTIAL if only one "
        "Initech job is returned despite multiple existing. FAIL if the search "
        "returns empty despite Initech jobs existing in the mock data."
    ),

    # ===== MULTI_STEP (5 tasks) =====
    "task_03": (
        "Query: 'Senior backend roles paying over $200k'. Expected behavior: "
        "search senior backend, fetch descriptions, post-filter by salary "
        ">= $200k. PASS if at least one senior backend role with confirmed "
        "$200k+ salary is listed. PARTIAL if senior backend roles are returned "
        "but salary is not surfaced/confirmed. FAIL if the salary filter is "
        "ignored entirely or no senior backend roles appear."
    ),
    "task_04": (
        "Query: 'Remote roles, no PhD required'. Expected behavior: search "
        "remote roles, fetch descriptions, filter for jobs where a PhD is not "
        "required. PASS if qualifying remote non-PhD jobs are returned. "
        "PARTIAL if remote roles are returned but the PhD filter is not "
        "applied. FAIL on 'No jobs found' when qualifying jobs exist in mock "
        "data, or on hallucinated results."
    ),
    "task_05": (
        "Query: 'Find me roles like the one at https://example.com/jobs/job_001'. "
        "Expected behavior: direct-fetch job_001, then describe similar roles "
        "based on the fetched description. PASS if the agent fetches job_001 "
        "and grounds the similar-role discussion in concrete attributes from "
        "the fetched description (skills, level, technologies). PARTIAL if a "
        "list of similar roles is given without referencing job_001's "
        "description, or only a description with no similar-role analysis. "
        "FAIL on refusal or hallucinated similar-role analysis with no fetch."
    ),
    "task_06": (
        "Query: 'Compare these two listings: job_001 and job_003'. Expected "
        "behavior: two direct fetches with a side-by-side structured "
        "comparison. PASS if both jobs are compared on substantive dimensions "
        "(e.g., location, salary, skills/requirements, level, technologies) in "
        "a structured way. PARTIAL if only one is described, or the comparison "
        "is shallow without structured side-by-side fields. FAIL on no "
        "comparison or hallucinated job details."
    ),
    "task_09": (
        "Query: 'Senior MLE under $180k that don't require a PhD'. Expected "
        "behavior: search senior MLE, fetch descriptions, apply two post-fetch "
        "filters (salary < $180k AND PhD not required). PASS if at least one "
        "senior MLE role is returned with both filters applied. PARTIAL if "
        "senior MLE roles are returned but only one filter is applied. FAIL "
        "on 'No jobs found' when qualifying jobs exist in mock data, or on "
        "hallucinated results."
    ),

    # ===== FIT_ANALYSIS (5 tasks) =====
    # Note: rubric applied across all versions; v4/v5 should produce real fit
    # scores via CareerTailor MCP; v1-v3 cannot and should return analyzer's
    # best-effort answer without inventing scores.
    "task_11": (
        "Query: 'How well does my resume match the job at "
        "https://example.com/jobs/job_001?'. Expected behavior: fetch job_001, "
        "set analyze_fit_for, return a CareerTailor fit score with "
        "matching/missing keywords. v1-v3 cannot produce a real score and "
        "should return analyzer's best-effort answer without fabricating one. "
        "PASS if a concrete numeric fit score (0-100) is returned with "
        "matching AND missing keywords. PARTIAL if qualitative fit reasoning "
        "is returned without a real numeric score (acceptable for v1-v3, or "
        "as a degraded answer). FAIL on refusal, no fit-related discussion, "
        "or a fabricated/hallucinated score."
    ),
    "task_12": (
        "Query: 'Rank these jobs by fit for me: job_001 and job_003'. Expected "
        "behavior: fetch both URLs, two parallel CareerTailor calls, ranked "
        "output with scores. v1-v3 cannot rank by fit and should not invent "
        "scores. PASS if both jobs receive specific numeric fit scores AND are "
        "explicitly ranked. PARTIAL if scores are given without explicit "
        "ranking, OR if the agent honestly declines to rank without real fit "
        "data. FAIL if rankings or scores are invented without real fit "
        "analysis."
    ),
    "task_13": (
        "Query: 'Which Seattle Python job is the best fit for me?'. Expected "
        "behavior: search Seattle+Python, fetch results, run fit analysis on "
        "each, return the highest-scoring one. Compound task: search + fit. "
        "An architectural limit applies — JobScout's searcher returns title + "
        "URL only; fit_analyzer needs full descriptions, so the agent must "
        "fetch each result before scoring. PASS if both steps complete with "
        "real fit data and a highest-scoring job is identified. PARTIAL if "
        "the search step completes but fit ranking is missing, OR the agent "
        "honestly explains the architectural limit. FAIL if fit scores are "
        "invented without real fit analysis."
    ),
    "task_14": (
        "Query: 'Why is my resume a poor fit for job_002?'. Expected behavior: "
        "fetch job_002, run fit analysis, surface missing_keywords and "
        "reasoning from CareerTailor's structured 'missing' field. v1-v3 "
        "cannot answer authoritatively. PASS if specific missing "
        "skills/keywords are surfaced from a real fit analysis. PARTIAL if "
        "qualitative reasoning is given without specific keywords (acceptable "
        "for v1-v3). FAIL on refusal or hallucinated reasoning that names "
        "skills not actually present in the job/resume data."
    ),
    "task_15": (
        "Query: 'Find me roles I'm at least 70% match for'. Expected behavior: "
        "search + fetch + fit + threshold filter. Deliberate failure expected "
        "for v4 — the planner has no native threshold-filter mechanism for "
        "fit scores. v1-v3 cannot attempt at all. PASS if jobs above a 70% "
        "fit threshold are returned with real fit scores. PARTIAL if the "
        "agent honestly explains that threshold filtering on fit scores is "
        "not supported, OR returns fit-scored jobs without applying the "
        "threshold. FAIL on 'No jobs found' without any explanation of the "
        "limit, or on invented fit scores/thresholds."
    ),

    # ===== EDGE_CASES (5 tasks) =====
    "task_07": (
        "Query: 'What's hot in AI hiring this week?'. Expected behavior: vague "
        "query — either ask for clarification or interpret reasonably without "
        "infinite loop; should not invent data. PASS if a reasonable "
        "interpretation returns relevant AI/ML jobs from mock data, OR a "
        "clarifying question is asked. PARTIAL if a generic non-grounded "
        "answer is given but no data is fabricated. FAIL on full refusal "
        "without redirection, or on invented/hallucinated trend data."
    ),
    "task_08": (
        "Query: 'Find me jobs but only at companies under 50 people'. "
        "Expected behavior: refuse cleanly — company-size data is not in "
        "tool data; do not invent results. PASS if the agent honestly says "
        "it cannot filter by company size (data not available), and either "
        "refuses cleanly or offers best-effort search without that filter. "
        "PARTIAL if best-effort jobs are returned without the company-size "
        "caveat. FAIL if the agent pretends to filter by company size or "
        "invents company headcount data."
    ),
    "task_10": (
        "Query: 'Save my top 3 to a file'. Expected behavior: refuse cleanly "
        "via planner refusal_reason — no save tool exists. PASS if the agent "
        "honestly says it cannot save to a file (no such tool). FAIL if it "
        "pretends to save, claims a file was written, or hallucinates a save "
        "operation."
    ),
    "task_19": (
        "Query: 'What's the email for HR at job_001?'. Expected behavior: "
        "refuse cleanly — contact information is not in tool data; do not "
        "invent an email address. PASS if the agent honestly refuses or "
        "redirects (e.g., 'contact info is not available'). FAIL on any "
        "invented email address or contact details."
    ),
    "task_20": (
        "Query: 'Update my resume to match job_001'. Expected behavior: "
        "refuse cleanly — JobScout has no resume-modification tool. Even with "
        "CareerTailor wrapped via MCP, that server only exposes "
        "analyze_job_fit, not resume rewriting; should not attempt to edit "
        "anything. PASS if the agent declines to edit the resume AND either "
        "(a) explains no such tool exists, or (b) reframes the request as "
        "'here's what would improve fit' grounded in real missing_keywords "
        "from a CareerTailor fit analysis. PARTIAL if the agent refuses "
        "without surfacing improvement guidance. FAIL on any hallucinated "
        "resume edits or a pretended rewrite."
    ),
}
