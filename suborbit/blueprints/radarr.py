from flask import Blueprint, jsonify
import requests, time
from ..config import Config

radarr_bp = Blueprint("radarr", __name__)

_cache = {"timestamp": 0, "data": None}
_CACHE_TTL = 600  # seconds (10 minutes)


def radarr_base_url():
    """Return the Radarr UI root (strip trailing /api/* if present)."""
    api_url = Config.RADARR_API.rstrip("/")
    if "/api" in api_url:
        api_url = api_url.rsplit("/api", 1)[0]
    return api_url


@radarr_bp.route("/api/radarr/recent")
def recent():
    """Return recently added movies from Radarr (cached for 10 min)."""
    now = time.time()
    if _cache["data"] and now - _cache["timestamp"] < _CACHE_TTL:
        return jsonify(_cache["data"])

    api_url = Config.RADARR_API.rstrip("/")
    api_key = Config.RADARR_KEY  # ✅ correct variable name

    if not api_url or not api_key:
        return jsonify({"error": "Radarr not configured"}), 400

    try:
        url = f"{api_url}/movie"
        headers = {"X-Api-Key": api_key}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        movies = r.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    movies = sorted(movies, key=lambda m: m.get("added", ""), reverse=True)
    base_ui = radarr_base_url()

    recent = []
    for m in movies[:10]:
        # Poster image
        img = ""
        for i in m.get("images", []):
            if i.get("coverType") == "poster":
                path = i.get("remoteUrl") or i.get("url")
                if path:
                    img = path if path.startswith("http") else f"{base_ui}{path}"
                    break

        # Ratings
        rating = None
        ratings = m.get("ratings", {})
        if "imdb" in ratings and ratings["imdb"].get("value"):
            rating = ratings["imdb"]["value"]
        elif "tmdb" in ratings and ratings["tmdb"].get("value"):
            rating = ratings["tmdb"]["value"]

        # URLs
        tmdb_id = m.get("tmdbId")
        imdb_id = m.get("imdbId")

        base_ui = radarr_base_url()
        radarr_url = (
            f"{base_ui}/movie/{tmdb_id or m.get('id')}"
            if (tmdb_id or m.get("id"))
            else None
        )
        tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}" if tmdb_id else None
        imdb_url = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else None

        recent.append(
            {
                "title": m.get("title"),
                "year": m.get("year"),
                "rating": rating,
                "poster": img,
                "overview": m.get("overview", ""),
                "radarr": radarr_url,
                "tmdb": tmdb_url,
                "imdb": imdb_url,
            }
        )

    _cache["timestamp"] = now
    _cache["data"] = recent
    return jsonify(recent)


@radarr_bp.route("/api/radarr/refresh", methods=["POST"])
def refresh_cache():
    """Manually clear Radarr poster cache."""
    global _cache
    _cache = {"timestamp": 0, "data": None}
    return jsonify({"status": "cleared"})
