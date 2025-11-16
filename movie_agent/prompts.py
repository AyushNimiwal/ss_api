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



SHARED_USR_REQUEST_PROMPT = """
USER_REQUEST:
{req}

Treat as:
- hard filter if explicit
- strong preference if vague
""".strip()


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