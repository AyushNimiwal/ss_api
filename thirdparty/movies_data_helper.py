import requests
import random
from datetime import datetime, timedelta
from .app_constants import SEARCH_TITLES_QUERY, DETAILS_QUERY, SEARCH_RELEASE_QUERY
from movie_agent.models import UserContent, Content
from movie_agent.app_settings import ContentType


API_URL = "https://apis.justwatch.com/graphql"

country = "IN"
language = "hi"
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/127.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.justwatch.com",
    "Referer": "https://www.justwatch.com/"
})

def _post(query, variables):
    try:
        resp = session.post(
            API_URL,
            json={"query": query, "variables": variables}
        )
        resp.raise_for_status()
    except Exception as e:
        print("❌ Request failed:", e)
        if resp is not None:
            print(resp.text[:500])
        return None
    try:
        return resp.json().get("data")
    except Exception:
        print("⚠️ Invalid JSON response")
        print(resp.text[:500])
        return None

def weighted_shuffle(items):
    # More recently released items get slightly higher weight
    def weight(i):
        rd = i.get("release_date") or "1900-01-01"
        return datetime.strptime(rd, "%Y-%m-%d").timestamp()

    return sorted(items, key=lambda x: weight(x) + random.random() * 1e12, reverse=True)

def search_movies(title=None, genre=None, country="IN", language="hi", 
    year_from=None, year_until=None, limit=10):
    filter_dict = {}
    if title:
        filter_dict["searchQuery"] = title
    if genre:
        filter_dict["genres"] = genre
    if not filter_dict:
        filter_dict["searchQuery"] = ""

    variables = {
        "searchTitlesFilter": filter_dict,
        "country": country,
        "language": language,
        "first": max(30, limit),
        "sortBy": "POPULAR"
    }
    data = _post(SEARCH_TITLES_QUERY, variables)
    if not data:
        return []
    profile = "s718"  # poster size
    b_profile = "s1440" # backdrop poster size
    format_ = "webp" # image format
    results = []
    for edge in data.get("popularTitles", {}).get("edges", []):
        node = edge["node"]
        content = node.get("content", {})
        year = content.get("originalReleaseYear")
        if (year_from and (year is None or year < year_from)) or \
            (year_until and (year is None or year > year_until)):
            continue
        poster_template = content.get("posterUrl")
        poster_url = (
            f"https://images.justwatch.com{poster_template.replace('{profile}', profile).replace('{format}', format_)}"
            if poster_template else None
        )

        backdrop_list = content.get("backdrops", [])
        backdrop_urls = [
            f"https://images.justwatch.com{b.get('backdropUrl').replace('{profile}', b_profile).replace('{format}', format_)}"
            for b in backdrop_list if b.get("backdropUrl")
        ]
        
        results.append({
            "title": content.get("title"),
            "description": content.get("shortDescription"),
            "year": year,
            "runtime": content.get("runtime"),
            "genres": [g["shortName"] for g in content.get("genres", [])],
            "imdbId": content.get("externalIds", {}).get("imdbId"),
            "tmdbId": content.get("externalIds", {}).get("tmdbId"),
            "age": content.get("ageCertification"),
            "content_type": node.get("objectType"),
            "id": node.get("id"),
            "release_date": content.get("originalReleaseDate"),
            "posterUrl": poster_url,
            "backdropUrl": backdrop_urls
        })
    random_pool = weighted_shuffle(results[: limit * 3])
    return random_pool[:limit]


def get_movies_for_user(user_id, title=None, genre=None, country="IN", language="hi",
     year_from=None, year_until=None, limit=10):
    """
    Search movies or shows on JustWatch with optional filters and return recent releases first.

    Args:
        user_id(int): User id from user object
        title (str, optional): Movie or show title keyword to search for.
        genre (list[str], optional): Genre(s) to filter (e.g., ["act", "drm"]).
        country (str, optional): Specific country of movie production
        language (str, optional): Specific language of movie (e.g., hi, en)
        year_from (int, optional): Minimum release year (filter applied in Python after fetching).
        year_until (int, optional): Maximum release year (filter applied in Python after fetching).
        limit (int, optional): Maximum number of results to return. Defaults to 10.

    Returns:
        list[dict]: A list of movies/shows matching the filters, sorted by release date (newest first).
            Each dictionary contains:
                - "title" (str): Movie/show title
                - "description" (str): Short synopsis
                - "year" (int): Original release year
                - "runtime" (int): Duration in minutes
                - "genres" (list[str]): List of genre short names
                - "imdbId" (str): IMDb identifier (if available)
                - "tmdbId" (str): TMDb identifier (if available)
                - "age" (str): Age certification
                - "content_type" (str): Type of object (MOVIE or SHOW)
                - "id" (str): Unique JustWatch identifier
                - "release_date" (str): Original release date in "YYYY-MM-DD"
                - "poster_url" (list[str]): List of poster images url
                - "backdrop_url" (list[str]): List of backdrop images url
    """
    watched_ids = set(UserContent.objects.filter(user_id=user_id, watched=True)
        .values_list('content__imdbId', flat=True))
    batch_limit = limit * 3
    candidates = search_movies(title, genre, country, language, year_from, 
        year_until, limit=batch_limit)
    unwatched = [m for m in candidates if m['imdbId'] not in watched_ids]
    while len(unwatched) < limit:
        batch_limit *= 2
        more_candidates = search_movies(title, genre, country, language, 
            year_from, year_until, limit=batch_limit)
        new_unwatched = [m for m in more_candidates if m['imdbId'] not in 
            watched_ids and m['imdbId'] not in {x['imdbId'] for x in unwatched}]
        if not new_unwatched:
            break
        unwatched.extend(new_unwatched)
    random_pool = weighted_shuffle(unwatched[: limit * 3])
    result = random_pool[:limit]
    crt_contents = {}
    qry = Content.objects.filter(justwatchId__in=[c['id'] for c in result])
    existing_ids = set(qry.values_list('justwatchId', flat=True))
    for content in result:
        if content.get("id") in existing_ids:
            continue
        if content.get("content_type") == "MOVIE":
            content_type = ContentType.MOVIE
        else:
            content_type = ContentType.SHOW
        crt_contents[content.get("id")] = Content(
            title=content.get("title"),
            description=content.get("description"),
            release_date=content.get("release_date"),
            content_type=content_type,
            imdbId=content.get("imdbId"),
            tmdbId=content.get("tmdbId"),
            justwatchId=content.get("id"),
            genres=content.get("genres"),
            posterUrl=content.get("posterUrl"),
            backdropUrl=content.get("backdropUrl", [])
        )
    res = Content.objects.bulk_create(crt_contents.values(), batch_size=500)
    all_content = list(res) + list(qry)
    user_content_payload = [
        UserContent(user_id=user_id, content_id=c.id)
        for c in all_content
    ]
    UserContent.objects.bulk_create(
        user_content_payload,
        batch_size=500,
        ignore_conflicts=True
    )
    cnt_ids = [c.id for c in all_content]
    final_res = UserContent.objects.filter(
        user_id=user_id,
        content_id__in=cnt_ids
    )
    return final_res

def get_movie_details(movie_id):
    variables = {
        "nodeId": movie_id,
        "country": country,
        "language": language
    }
    data = _post(DETAILS_QUERY, variables)
    if not data:
        return None

    node = data.get("node")
    if not node:
        return None
    content = node.get("content", {})
    return {
        "title": content.get("title"),
        "description": content.get("shortDescription"),
        "year": content.get("originalReleaseYear"),
        "runtime": content.get("runtime"),
        "genres": [g["shortName"] for g in content.get("genres", [])],
        "imdbId": content.get("externalIds", {}).get("imdbId"),
        "tmdbId": content.get("externalIds", {}).get("tmdbId"),
        "age": content.get("ageCertification"),
        "scoring": content.get("scoring"),
        "objectType": node.get("objectType"),
        "id": node.get("id")
    }

        # --- Function: Get all available genres ---

def search_by_date_range(days_from=None, days_until=None, limit=10):
    """
    Fetch movies released within a date range relative to today.

    Args:
        days_from (int, optional): Days before today for start of range.
        days_until (int, optional): Days after today for end of range.
        limit (int, optional): Max number of results. Defaults to 10.

    Returns:
        list[dict]: Movies with title, description, release date, genres, and ID.
    """
    variables = {
        "country": country,
        "language": language,
        "first": limit
    }
    data = _post(SEARCH_RELEASE_QUERY, variables)
    if not data:
        return []

    today = datetime.today().date()
    start_date = today + timedelta(days=days_from) if days_from is not None else None
    end_date = today + timedelta(days=days_until) if days_until is not None else None

    results = []
    print("DATA", data)
    for edge in data.get("newTitles", {}).get("edges", []):
        node = edge["node"]
        content = node.get("content", {})
        release_str = content.get("originalReleaseDate")
        if not release_str:
            continue
        try:
            release_date = datetime.strptime(release_str, "%Y-%m-%d").date()
        except Exception:
            continue

        if (start_date and release_date < start_date) or (end_date and release_date > end_date):
            continue

        results.append({
            "title": content.get("title"),
            "description": content.get("shortDescription"),
            "releaseDate": release_str,
            "genres": [g["shortName"] for g in content.get("genres", [])],
            "id": node.get("id")
        })

    return results




# print("\n🔍 Search by Title:")
# # movies = search_movies("genre:fam,drm; limit:5")
# movies = search_movies.invoke({"genre": ['adv'], "limit": 1})
# print(movies)

# if movies:
#     print("\n🎬 Full Details of First Movie:")
#     details = jw.get_movie_details(movies[0]["id"])
#     print(details)


# upcoming = jw.search_by_date_range(days_from=0, days_until=14)
# print("🎬 Upcoming in next 2 weeks:")
# for m in upcoming:
#     print(m)

# # Last 7 days
# last_week = jw.search_by_date_range(days_from=-7, days_until=0)
# print("\n🎬 Released last week:")
# for m in last_week:
#     print(m)

# # Last 3 weeks
# last_3_weeks = jw.search_by_date_range(days_from=-21, days_until=0)
# print("\n🎬 Released last 3 weeks:")
# for m in last_3_weeks:
#     print(m)