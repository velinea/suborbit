# suborbit_core.py
# Cleaned, sequential core suitable for CLI or Flask UI import

import csv, json, os, time, random, threading
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import requests

from .config import Config


from suborbit.blueprints.radarr import mark_radarr_updated


# ----------------- Stop mechanism -----------------
def check_stop():
    if STOP_EVENT.is_set():
        raise RuntimeError("Stop requested")


# ----------------- Paths -----------------
docker_config = Path("/config")
local_config = Path("config")

# Decide base directory
if docker_config.exists() and docker_config.is_dir():
    BASE_CONFIG = docker_config
else:
    local_config.mkdir(exist_ok=True)
    BASE_CONFIG = local_config

# Now define paths relative to that base
LOG_PATH = BASE_CONFIG / "suborbit.log"
CACHE_FILE = BASE_CONFIG / "cache.json"
CSV_FILE = BASE_CONFIG / "suborbit.csv"


# ----------------- Logging -----------------
def log(msg: str) -> None:
    if not Config.QUIET_MODE:
        print(msg, flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        # Logging should never crash the run
        pass


# ----------------- Cache -----------------
def load_cache() -> Dict[str, Any]:
    if CACHE_FILE and Path(CACHE_FILE).exists():
        try:
            with Path(CACHE_FILE).open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, Any]) -> None:
    try:
        Path(CACHE_FILE).parent.mkdir(parents=True, exist_ok=True)
        with Path(CACHE_FILE).open("w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"[WARN] Failed to save cache: {e}")


# ----------------- HTTP helpers -----------------
SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})


def http_get(
    url: str, *, params: dict = None, headers: dict = None, timeout: int = 15
) -> Optional[requests.Response]:
    try:
        resp = SESSION.get(
            url, params=params or {}, headers=headers or {}, timeout=timeout
        )
        return resp
    except Exception as e:
        log(f"[HTTP] GET failed {url}: {e}")
        return None


def http_post(
    url: str, *, json_body: dict, headers: dict = None, timeout: int = 20
) -> Optional[requests.Response]:
    try:
        resp = SESSION.post(url, json=json_body, headers=headers or {}, timeout=timeout)
        return resp
    except Exception as e:
        log(f"[HTTP] POST failed {url}: {e}")
        return None


# ----------------- API: TMDB -----------------
def tmdb_details(tmdb_id: int) -> Optional[dict]:
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    resp = http_get(url, params={"api_key": Config.TMDB_API_KEY, "language": "en-US"})
    if not resp or resp.status_code != 200:
        if Config.DEBUG:
            log(f"[TMDB] details {tmdb_id} status={getattr(resp, 'status_code', None)}")
        return None
    return resp.json()


def tmdb_discover(year: int, page: int = 1) -> List[dict]:
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": Config.TMDB_API_KEY,
        "primary_release_year": year,
        "sort_by": "popularity.desc",
        "page": page,
    }
    resp = http_get(url, params=params)
    if not resp or resp.status_code != 200:
        if Config.DEBUG:
            log(
                f"[TMDB] discover {year} p{page} status={getattr(resp, 'status_code', None)}"
            )
        return []
    return resp.json().get("results", [])


# ----------------- API: OMDb (IMDb + RottenTomatoes) -----------------
def omdb_ratings(imdb_id: str) -> Tuple[Optional[float], Optional[int], Optional[int]]:
    """
    Returns: (imdb_rating, imdb_votes, rt_score)
    """
    if not (imdb_id and Config.OMDB_KEY):
        return None, None, None
    resp = http_get(
        "http://www.omdbapi.com/",
        params={"i": imdb_id, "apikey": Config.OMDB_KEY},
    )
    if not resp or resp.status_code != 200:
        if Config.DEBUG:
            log(f"[OMDb] status={getattr(resp, 'status_code', None)} imdb={imdb_id}")
        return None, None, None
    data = resp.json()
    imdb_rating = None
    imdb_votes = None
    rt_score = None
    try:
        if data.get("imdbRating") and data["imdbRating"] != "N/A":
            imdb_rating = float(data["imdbRating"])
        if data.get("imdbVotes") and data["imdbVotes"] != "N/A":
            imdb_votes = int(data["imdbVotes"].replace(",", ""))
        for r in data.get("Ratings", []):
            if r.get("Source") == "Rotten Tomatoes":
                rt_score = int(r.get("Value", "0").replace("%", ""))
    except Exception:
        pass
    return imdb_rating, imdb_votes, rt_score


# ----------------- API: OpenSubtitles -----------------
def has_subs(subtitle_lang: str, imdb_id: int) -> bool:
    """
    Check OpenSubtitles for subtitles that are not AI/machine translated.
    """
    headers = {"Api-Key": Config.OS_API_KEY, "User-Agent": "SubOrbit/1.0"}
    params = {
        "languages": subtitle_lang,
        "imdb_id": imdb_id,
        "type": "movie",
        "ai_translated": "exclude",
        "machine_translated": "exclude",
    }
    resp = http_get(
        "https://api.opensubtitles.com/api/v1/subtitles", params=params, headers=headers
    )
    if not resp or resp.status_code != 200:
        if Config.DEBUG:
            log(f"[OS] imdb_id={imdb_id} status={getattr(resp, 'status_code', None)}")
        return False
    data = resp.json()
    time.sleep(Config.OS_DELAY)  # be gentle to OS API
    return len(data.get("data", [])) > 0


# ----------------- API: Radarr -----------------
def radarr_exists(tmdb_id: int) -> bool:
    url = f"{Config.RADARR_API}/movie"
    headers = {"X-Api-Key": Config.RADARR_KEY}
    resp = http_get(url, params={"tmdbId": tmdb_id}, headers=headers)
    if not resp or resp.status_code != 200:
        return False
    try:
        return len(resp.json()) > 0
    except Exception:
        return False


def radarr_add(
    tmdb_id: int, title: str, root_folder: str = Config.ROOT_FOLDER
) -> Tuple[bool, str]:
    url = f"{Config.RADARR_API}/movie"
    headers = {"X-Api-Key": Config.RADARR_KEY}
    payload = {
        "tmdbId": tmdb_id,
        "qualityProfileId": Config.QUALITY_PROFILE_ID,
        "title": title,
        "titleSlug": str(tmdb_id),
        "rootFolderPath": root_folder,
        "monitored": True,
        "addOptions": {"searchForMovie": bool(Config.SEARCH_FOR_MOVIE)},
    }
    resp = http_post(url, json_body=payload, headers=headers)
    if not resp:
        return False, "no response"
    if resp.status_code == 201:
        return True, "added"
    text = resp.text or ""
    # tolerate 'already exists' semantics
    if resp.status_code in (400, 405) and (
        "MovieExistsValidator" in text or "been added" in text
    ):
        return False, "exists"
    return False, f"status={resp.status_code} {text[:200]}"


# ----------------- CSV -----------------
def append_csv(row: Dict[str, Any]) -> None:
    file = Path(CSV_FILE)
    is_new = not file.exists()
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "year",
                "tmdb_id",
                "imdb_id",
                "original_language",
                "genres",
                "tmdb_rating",
                "imdb_rating",
                "rt_score",
                "vote_count",
            ],
        )
        if is_new:
            writer.writeheader()
        writer.writerow(row)


# ----------------- Pipeline -----------------
def discover_candidates_for_year(year: int, pages: int = 3) -> List[dict]:
    """
    Discover popular TMDB movies for a year; we’ll later filter subtitles.
    """
    results: List[dict] = []
    for p in range(1, pages + 1):
        page = tmdb_discover(year, page=p)
        results.extend(page)
    return results


def enrich_movie_basic(tmdb_obj: dict) -> Optional[dict]:
    """
    From TMDB discover item -> fetch details and produce a normalized movie dict.
    Note: id from TMDB discover is 'id', from trakt list it's 'tmdb_id'.
    """
    tmdb_id = tmdb_obj.get("id") or tmdb_obj.get("tmdb_id")
    details = tmdb_details(tmdb_id)
    if not details:
        return None

    title = details.get("title") or details.get("original_title") or ""
    release_date = details.get("release_date") or "0000-00-00"
    try:
        year = (
            int(release_date[:4]) if release_date and release_date[0:4].isdigit() else 0
        )
    except Exception:
        year = 0
    imdb_id = details.get("imdb_id")
    original_language = details.get("original_language") or ""
    genres = [g.get("name", "") for g in (details.get("genres") or [])]
    tmdb_rating = (details.get("vote_average") or 0.0) * 1.0
    vote_count = int(details.get("vote_count") or 0)
    # log(
    #     f"Title: {title}, Year: {year}, Orig lang: {original_language}, Genres: {genres}"
    # )
    return {
        "title": title,
        "year": year,
        "tmdb_id": tmdb_id,
        "imdb_id": imdb_id,
        "original_language": original_language,
        "genres": genres,
        "tmdb_rating": float(tmdb_rating),
        "imdb_rating": None,
        "rt_score": None,
        "vote_count": vote_count,
    }


def get_tmdb_genres():
    if not Config.TMDB_API_KEY:
        return []
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={Config.TMDB_API_KEY}&language=en-US"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return [g["name"] for g in data.get("genres", [])]
    except Exception as e:
        print("Error fetching TMDB genres:", e)
        return []


def enrich_with_imdb_rt(movie: dict, cache: Dict[str, Any]) -> dict:
    """
    Optionally fetch IMDb + RT via OMDb (cached by imdb_id).
    """
    imdb_id = movie.get("imdb_id")
    if not imdb_id:
        return movie

    cache_key = f"omdb:{imdb_id}"
    if cache_key in cache:
        omdb = cache[cache_key]
        movie["imdb_rating"] = omdb.get("imdb_rating")
        movie["rt_score"] = omdb.get("rt_score")
        # allow cached imdb_votes to override low tmdb vote_count
        if omdb.get("imdb_votes") and (
            movie.get("vote_count", 0) < Config.MIN_VOTE_COUNT
        ):
            movie["vote_count"] = omdb["imdb_votes"]
        return movie

    imdb_rating, imdb_votes, rt_score = omdb_ratings(imdb_id)
    if imdb_rating is not None:
        movie["imdb_rating"] = imdb_rating
    if rt_score is not None:
        movie["rt_score"] = rt_score
    if imdb_votes:
        # if present, prefer IMDb votes for stability
        movie["vote_count"] = imdb_votes or movie.get("vote_count", 0)

    cache[cache_key] = {
        "imdb_rating": movie.get("imdb_rating"),
        "rt_score": movie.get("rt_score"),
        "imdb_votes": imdb_votes,
    }
    return movie


def fails_filters(
    movie,
    start_year,
    end_year,
    min_tmdb,
    min_imdb,
    min_rt,
    include_genres=None,
    exclude_genres=None,
):
    """
    Check movie against filters.
    Return reason string if it fails, else None.

    log(
        f"Checking filters for movie: {movie}, {start_year}, {end_year}, {min_tmdb}, {min_imdb}, {min_rt}, {genres}"
    )
    """

    try:
        year = int(movie.get("year", 0) or 0)
    except Exception:
        return "missing or invalid year"

    # Year filters
    if year < start_year:
        return f"too old (year {year} < {start_year})"
    if year > end_year:
        return f"too new (year {year} > {end_year})"

    # Votes filter
    vote_count = int(movie.get("vote_count", 0) or 0)
    if vote_count < Config.MIN_VOTE_COUNT:
        return f"too few votes ({vote_count} < {Config.MIN_VOTE_COUNT})"

    # Rating filters
    if Config.USE_TMDB:
        tmdb_rating = float(movie.get("tmdb_rating") or 0)
        if tmdb_rating < min_tmdb:
            return f"low TMDB ({tmdb_rating} < {min_tmdb})"

    if Config.USE_IMDB:
        imdb_rating = float(movie.get("imdb_rating") or 0)
        if imdb_rating < min_imdb:
            return f"low IMDB ({imdb_rating} < {min_imdb})"

    if Config.USE_RT:
        rt_score = int(movie.get("rt_score") or 0)
        if rt_score < min_rt:
            return f"low RT ({rt_score} < {min_rt})"

    # Genres
    movie_genres = [g.lower() for g in movie.get("genres", [])]

    if include_genres:
        if not any(g in movie_genres for g in include_genres):
            return f"no required genres (movie has {movie_genres}, wanted {include_genres})"

    if exclude_genres:
        if any(g in movie_genres for g in exclude_genres):
            return f"excluded genre present (movie has {movie_genres}, excludes {exclude_genres})"

    return None


# ----------------- API: Trakt -----------------

import re


def sanitize_trakt_name(name: str) -> str:
    """
    Sanitize a Trakt username or list name for API use.
    - lowercase
    - replace spaces/underscores with '-'
    - remove special characters
    """
    if not name:
        return ""
    # lowercase and trim
    name = name.strip().lower()
    # spaces & underscores to dash
    name = re.sub(r"[\s_]+", "-", name)
    # keep only letters, numbers, dash
    name = re.sub(r"[^a-z0-9-]", "", name)
    return name


TOKEN_PATH = Path("trakt_token.json")


def get_trakt_token():
    """Return a valid Trakt access token (refresh if expired), with logging."""
    if not TOKEN_PATH.exists():
        log("ℹ️ No Trakt token found (public lists only).")
        return None

    with TOKEN_PATH.open("r", encoding="utf-8") as f:
        token_data = json.load(f)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    created_at = token_data.get("created_at", 0)
    expires_in = token_data.get("expires_in", 0)

    if time.time() < created_at + expires_in - 60:
        log("🔑 Using cached Trakt access token.")
        return access_token

    # Refresh
    log("♻️ Refreshing expired Trakt token ...")
    url = "https://api.trakt.tv/oauth/token"
    payload = {
        "refresh_token": refresh_token,
        "client_id": Config.TRAKT_CLIENT_ID,
        "client_secret": Config.TRAKT_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    headers = {"Content-Type": "application/json"}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code != 200:
            log(f"⚠️ Failed to refresh Trakt token: {r.status_code} {r.text[:200]}")
            return None
        new_data = r.json()
        new_data["created_at"] = int(time.time())

        with TOKEN_PATH.open("w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2)

        log("✅ Trakt token refreshed successfully.")
        return new_data["access_token"]
    except Exception as e:
        log(f"❌ Error refreshing Trakt token: {e}")
        return None


def fetch_trakt_list(user: str, list_name: str):
    """Fetch a (public or private) Trakt list of movies, with logging."""
    log(f"🎬 Fetching movies from Trakt list: {user}/{list_name}")

    user = sanitize_trakt_name(user)
    list_name = sanitize_trakt_name(list_name)
    url = f"https://api.trakt.tv/users/{user}/lists/{list_name}/items/movies"

    token = get_trakt_token()

    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": Config.TRAKT_CLIENT_ID,
        "User-Agent": "suborbit",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        log(f"🔗 Requesting: {url}")
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            log(f"⚠️ Trakt returned {r.status_code}: {r.text[:200]}")
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log(f"❌ Trakt fetch failed: {e}")
        return []

    movies = []
    for item in data:
        m = item.get("movie")
        if not m:
            continue
        ids = m.get("ids", {})
        movies.append(
            {
                "title": m.get("title"),
                "year": m.get("year"),
                "imdb_id": ids.get("imdb"),
                "tmdb_id": ids.get("tmdb"),
            }
        )

    return movies


# ----------------- Stop mechanism -----------------
# Global stop flag
STOP_EVENT = threading.Event()


def request_stop():
    """Call this to stop the current run gracefully."""
    STOP_EVENT.set()


def reset_stop():
    STOP_EVENT.clear()


# ----------------- Orchestration -----------------
def main_process(
    start_year: int = Config.START_YEAR,
    end_year: int = Config.END_YEAR,
    include_genres: Optional[list[str]] = None,
    exclude_genres: Optional[list[str]] = None,
    min_tmdb: float = Config.MIN_TMDB_RATING,
    min_imdb: float = Config.MIN_IMDB_RATING,
    min_rt: int = Config.MIN_RT_SCORE,
    max_movies: int = Config.MAX_MOVIES_PER_RUN,
    randomize: bool = Config.RANDOM_SELECTION,
    max_pages: int = Config.MAX_DISCOVER_PAGES,
    min_vote_count: int = Config.MIN_VOTE_COUNT,
    subtitle_lang: str = Config.SUBTITLE_LANG,
    trakt_user=None,
    trakt_list=None,
) -> None:
    """
    Runs the whole pipeline with current config and parameters.
    """

    # Make sure we start clean
    reset_stop()

    try:

        # Clear previous log
        try:
            LOG_PATH.write_text("", encoding="utf-8")
        except Exception:
            pass

        log(f"=== Starting SubOrbit run ===")
        log(f"Years: {start_year}–{end_year}")
        tmdb_min = str(min_tmdb) if Config.USE_TMDB else f"({min_tmdb})"
        imdb_min = str(min_imdb) if Config.USE_IMDB else f"({min_imdb})"
        rt_min = str(min_rt) if Config.USE_RT else f"({min_rt})"
        log(f"Min ratings: TMDB {tmdb_min}, IMDB {imdb_min}, RT {rt_min}")
        log(f"Max movies: {max_movies}")
        log(f"Randomize: {randomize}")
        log(f"Max TMDB pages per year: {max_pages}")
        log(f"Min TMDB/IMDB vote count: {min_vote_count}")
        if include_genres or exclude_genres:
            log(f"Include genres: {include_genres or 'none'}")
            log(f"Exclude genres: {exclude_genres or 'none'}")
        log(f"=============================")

        cache = load_cache()
        total_added = 0
        years = list(range(int(start_year), int(end_year) + 1))
        trakt_complete = False

        for year in years:
            if max_movies and total_added >= max_movies:
                break
            if trakt_complete:
                break

            # ----------------- Movie discovery -----------------
            if trakt_user and trakt_list:
                candidates = fetch_trakt_list(trakt_user, trakt_list)

                # Optional shuffle for variety
                if randomize and isinstance(candidates, dict):
                    import random

                    items = list(candidates.items())
                    random.shuffle(items)
                    candidates = dict(items)

                log(f"✅ Loaded {len(candidates)} movies from Trakt list.")
                trakt_complete = True
            else:
                log(f"-- Discovering TMDB movies for {year} ...")
                candidates = discover_candidates_for_year(
                    year, pages=Config.MAX_DISCOVER_PAGES
                )
                if randomize:
                    import random

                    random.shuffle(candidates)

            for item in candidates:
                if max_movies and total_added >= max_movies:
                    break

                check_stop()

                basic = enrich_movie_basic(item)
                if not basic:
                    continue

                # Optional genre override for this run (instead of ALLOWED_GENRES)
                # if genres:
                #     if not any(g in genres for g in basic.get("genres", [])):
                #         continue

                tmdb_id = basic.get("tmdb_id")
                imdb_id = basic.get("imdb_id")

                # Radarr pre-check
                if radarr_exists(tmdb_id):
                    log(f"📀 already in Radarr: {basic['title']}")
                    continue

                # IMDb/RT enrichment (cached)
                basic = enrich_with_imdb_rt(basic, cache)

                # Apply filters
                reason = fails_filters(
                    basic,
                    start_year,
                    end_year,
                    min_tmdb,
                    min_imdb,
                    min_rt,
                    include_genres=include_genres,
                    exclude_genres=exclude_genres,
                )
                if reason:
                    if Config.DEBUG:
                        log(f"❌ {reason}: {item.get('title','<no title>')}")
                    continue

                # Require subtitles (non-AI) before any rating fetch
                if not has_subs(subtitle_lang, imdb_id):
                    if Config.DEBUG:
                        log(f"❌ no {subtitle_lang} subs: {basic['title']}")
                    continue

                if Config.DEBUG:
                    log(f"✅ passed all filters: {item.get('title','<no title>')}")

                # Add to Radarr
                ok, msg = radarr_add(tmdb_id, basic["title"], Config.ROOT_FOLDER)
                if ok:
                    total_added += 1
                    mark_radarr_updated()
                    log(
                        f"🎬 added to Radarr: {basic['title']} ({basic['year']}) "
                        #                        f"| TMDb {basic.get('tmdb_rating')} | IMDb {basic.get('imdb_rating')} | RT {basic.get('rt_score')}"
                    )
                    append_csv(
                        {
                            "title": basic["title"],
                            "year": basic["year"],
                            "tmdb_id": basic["tmdb_id"],
                            "imdb_id": basic.get("imdb_id"),
                            "original_language": basic.get("original_language"),
                            "genres": ",".join(basic.get("genres", [])),
                            "tmdb_rating": basic.get("tmdb_rating"),
                            "imdb_rating": basic.get("imdb_rating"),
                            "rt_score": basic.get("rt_score"),
                            "vote_count": basic.get("vote_count", 0),
                        }
                    )
                elif msg == "exists":
                    log(f"Already in Radarr (detected on add): {basic['title']}")
                else:
                    log(f"[Radarr] Failed to add {basic['title']}: {msg}")

                # Persist cache periodically
                if total_added and total_added % 5 == 0:
                    save_cache(cache)

        save_cache(cache)
        log(f"=== Summary: added={total_added}, years={start_year}-{end_year} ===")
        mark_radarr_updated()

    except RuntimeError:
        log(f"Run stopped by user")


# ----------------- CLI -----------------
if __name__ == "__main__":
    # Purely parameter-driven: runs with values from config.py / .env
    main_process()
