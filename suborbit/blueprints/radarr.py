from flask import Blueprint, jsonify, request
import requests, time
from ..config import Config

radarr_bp = Blueprint("radarr", __name__)

# In-memory cache (10 min)
_cache = {"timestamp": 0, "data": None}
_CACHE_TTL = 600  # seconds


# ------------------------------------------------------------
# URL helpers
# ------------------------------------------------------------
def get_radarr_api():
    """
    Return the correct Radarr API root based on client network.
    Uses RADARR_API_LAN or RADARR_API_TAIL if defined, else RADARR_API.
    """
    client_ip = request.remote_addr or ""
    tail_ip = client_ip.startswith("100.") or client_ip.startswith("fd7a:")

    if tail_ip and getattr(Config, "RADARR_API_TAIL", None):
        return Config.RADARR_API_TAIL.rstrip("/")
    elif getattr(Config, "RADARR_API_LAN", None):
        return Config.RADARR_API_LAN.rstrip("/")
    else:
        return Config.RADARR_API.rstrip("/")


def radarr_base_url():
    """Return the Radarr UI root (strip trailing /api/* if present)."""
    api_url = get_radarr_api()
    if "/api" in api_url:
        api_url = api_url.rsplit("/api", 1)[0]
    return api_url


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@radarr_bp.route("/api/radarr/status")
def status():
    """Quick health check: verify Radarr connectivity and API key validity."""
    api_url = get_radarr_api()
    api_key = Config.RADARR_KEY

    if not api_url or not api_key:
        return jsonify({"ok": False, "error": "Radarr not configured"}), 400

    try:
        url = f"{api_url}/system/status"
        headers = {"X-Api-Key": api_key}
        r = requests.get(url, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json()
        return jsonify(
            {
                "ok": True,
                "name": data.get("appName", "Radarr"),
                "version": data.get("version"),
                "url": radarr_base_url(),
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@radarr_bp.route("/api/radarr/recent")
def recent():
    """Return recently added movies from Radarr (cached for 10 min)."""
    now = time.time()
    if _cache["data"] and now - _cache["timestamp"] < _CACHE_TTL:
        return jsonify(_cache["data"])

    api_url = get_radarr_api()
    api_key = Config.RADARR_KEY
    if not api_url or not api_key:
        return jsonify({"error": "Radarr not configured"}), 400

    try:
        url = f"{api_url}/movie"
        headers = {"X-Api-Key": api_key}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        movies = resp.json()
    except Exception as e:
        return jsonify({"error": f"Failed to reach Radarr: {e}"}), 500

    movies = sorted(movies, key=lambda m: m.get("added", ""), reverse=True)
    base_ui = radarr_base_url()

    recent = []
    for m in movies[:10]:
        # Poster
        img = ""
        for i in m.get("images", []):
            if i.get("coverType") == "poster":
                path = i.get("remoteUrl") or i.get("url")
                if path:
                    img = path if path.startswith("http") else f"{base_ui}{path}"
                    break

        # Ratings
        rating = None
        ratings = m.get("ratings") or {}
        if "imdb" in ratings and ratings["imdb"].get("value"):
            rating = ratings["imdb"]["value"]
        elif "tmdb" in ratings and ratings["tmdb"].get("value"):
            rating = ratings["tmdb"]["value"]
        elif ratings.get("value"):
            rating = ratings["value"]

        tmdb_id = m.get("tmdbId")
        imdb_id = m.get("imdbId")
        radarr_id = m.get("id")

        radarr_url = (
            f"{base_ui}/movie/{tmdb_id or radarr_id}"
            if (tmdb_id or radarr_id)
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
