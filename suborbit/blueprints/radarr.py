from flask import Blueprint, jsonify
import requests, time
from ..config import Config

radarr_bp = Blueprint("radarr", __name__)

# In-memory cache
_cache = {"timestamp": 0, "data": None}
_CACHE_TTL = 600  # seconds = 10 minutes


@radarr_bp.route("/api/radarr/recent")
def recent():
    """Return recently added movies from Radarr (cached for 10 min)."""
    now = time.time()
    # ✅ Use cache if valid
    if _cache["data"] and now - _cache["timestamp"] < _CACHE_TTL:
        return jsonify(_cache["data"])

    api_key = Config.RADARR_KEY
    base_url = Config.RADARR_API.rstrip("/")

    if not api_key or not base_url:
        return jsonify({"error": "Radarr not configured"}), 400

    try:
        url = f"{base_url}/movie"
        headers = {"X-Api-Key": api_key}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        movies = r.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Sort & map results
    movies = sorted(movies, key=lambda m: m.get("added", ""), reverse=True)

    recent = []
    for m in movies[:10]:
        img = ""
        for i in m.get("images", []):
            if i.get("coverType") == "poster":
                path = i.get("remoteUrl") or i.get("url")
                if path:
                    img = path if path.startswith("http") else f"{base_url}{path}"
                    break

        # Pick a rating (Radarr stores several, like IMDb or TMDb)
        rating = None
        ratings = m.get("ratings", {})
        if "imdb" in ratings and ratings["imdb"].get("value"):
            rating = ratings["imdb"]["value"]
        elif "tmdb" in ratings and ratings["tmdb"].get("value"):
            rating = ratings["tmdb"]["value"]

        # Build URLs
        tmdb_id = m.get("tmdbId")
        imdb_id = m.get("imdbId")
        radarr_id = m.get("id")

        tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}" if tmdb_id else None
        imdb_url = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else None
        radarr_url = f"{base_url}/movie/{radarr_id}" if radarr_id else None

        recent.append(
            {
                "title": m.get("title"),
                "year": m.get("year"),
                "rating": rating,
                "poster": img,
                "tmdb": tmdb_url,
                "imdb": imdb_url,
                "radarr": radarr_url,
            }
        )

    # ✅ Store in cache
    _cache["timestamp"] = now
    _cache["data"] = recent

    return jsonify(recent)


@radarr_bp.route("/api/radarr/refresh", methods=["POST"])
def refresh_cache():
    """Manually clear Radarr poster cache."""
    global _cache
    _cache["data"] = None
    _cache["timestamp"] = 0
    return jsonify({"status": "cleared"})
