SUGGESSTION_THROUGH_YT_DATA = """
You are a movie recommendation engine.

INPUT:
- yt: User's YouTube tastes (summary text below)
- hist: User watch history (optional JSON)
- req: User request (optional text)
- limit: {limit}
- GENRE_MAPPING: {genre_map}

TASK:
1. Infer top user preferences from `yt`:
   - topics, pacing, tone, creator types
   - likely movie genres (use GENRE_MAPPING keys only)

2. Produce a TOOL_QUERY JSON:
   Required keys:
   {{
     "title": string|null,
     "genre": [code, code]|null,
     "country": "IN",
     "language": "hi",
     "year_from": int|null,
     "year_until": int|null,
     "limit": {limit}
   }}
   Rules:
   - Use <=2 genre codes
   - Use GENRE_MAPPING codes only
   - No additional keys
   - Do NOT include user_id

3. Re-rank results conceptually using:
   - `hist` (avoid watched items)
   - `req` (filter/strong preference)
   - inferred taste

OUTPUT:
Return ONLY valid JSON for TOOL_QUERY.

USER YOUTUBE DATA:
{yt_data}

""".strip()


SHARED_USR_CNT_DATA_PROMPT = """
WATCH_HISTORY (JSON):
{hist}

Use only for:
- avoiding watched titles
- refining inferred preferences
- re-ranking relevance
""".strip()



SHARED_USR_REQUEST_PROMPT = """USER_REQUEST:
{req}

Interpret the user's text as STRICT search filters:

Rules:
1. If the request contains ANY descriptive word (e.g., funny, dark, thriller, romantic, adventure),
   map the word to BOTH:
   - title search ("searchQuery")
   - genre search (map using GENRE_MAPPING)

2. If the user mentions a year (e.g., 2020, 2018, 90s):
   - Set year_from and year_until equal to that year
   - If a range (e.g., 2010-2015), set year_from=2010, year_until=2015

3. If user mentions time periods ("recent", "new", "latest"):
   - Prefer recent release dates (last 2 years)

4. If multiple genres are implicitly suggested, include ALL as a list.

5. DO NOT ignore user query. Always map it into title or genre or both. 
   If unclear → put it in title search.

6. If conflicting, user request is a HARD FILTER.
"""


TOOL_SCHEMA = """
TOOL_QUERY FORMAT (return ONLY this JSON):
{
  "title": string|null,
  "genre": [str,str]|null,
  "country": "IN",
  "language": "hi",
  "year_from": int|null,
  "year_until": int|null,
  "limit": LIMIT
}
""".strip()

DEFAULT_TOOL_ARGS = {
    "title": None,
    "genre": None,
    "country": "IN",
    "language": "hi",
    "year_from": None,
    "year_until": None,
    "limit": 10,
}