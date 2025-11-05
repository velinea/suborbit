from flask import Blueprint, jsonify
import requests, time
from urllib.parse import urlparse
from ..config import Config

radarr_bp = Blueprint("radarr", __name__)

_cache_recent = {"timestamp": 0, "data": None}
_cache_status = {"timestamp": 0, "data": None}
_CACHE_TTL = 600
_STATUS_TTL = 300


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

import re, sys


def validate_radarr_config():
    """
    Validate RADARR_API and RADARR_HOST early on startup.
    Prints friendly console warnings but does not stop execution.
    """
    api = getattr(Config, "RADARR_API", "").strip()
    host = getattr(Config, "RADARR_HOST", "").strip()
    key = getattr(Config, "RADARR_KEY", "").strip()

    def warn(msg):
        print(f"⚠️  [SubOrbit:Radarr] {msg}", file=sys.stderr)

    # --- API sanity ---
    if not api:
        warn("RADARR_API is not set — Radarr integration will be disabled.")
        return

    if not api.startswith("http://") and not api.startswith("https://"):
        warn(f"RADARR_API '{api}' should start with http:// or https://")

    if not re.search(r"/api/v3/?$", api):
        warn(f"RADARR_API '{api}' should end with '/api/v3'")

    # --- HOST sanity ---
    if not host:
        warn("RADARR_HOST not set — using API hostname for UI links.")
    else:
        # Very basic hostname/IP check
        if not re.match(r"^[a-zA-Z0-9\.\-]+$", host):
            warn(
                f"RADARR_HOST '{host}' looks invalid. Expected FQDN or IP (no scheme)."
            )

    # --- KEY sanity ---
    if not key:
        warn("RADARR_KEY missing — API calls will fail with 401 Unauthorized.")


# Run validation at import
validate_radarr_config()


def fetch_status():
    """Fetch and cache /system/status from Radarr."""
    now = time.time()
    if _cache_status["data"] and now - _cache_status["timestamp"] < _STATUS_TTL:
        return _cache_status["data"], None

    api_url = Config.RADARR_API.rstrip("/")
    api_key = Config.RADARR_KEY
    if not api_url or not api_key:
        return None, ("Radarr not configured", 400)

    try:
        r = requests.get(
            f"{api_url}/system/status", headers={"X-Api-Key": api_key}, timeout=8
        )
        r.raise_for_status()
        data = r.json()
        _cache_status["timestamp"] = now
        _cache_status["data"] = data
        return data, None
    except Exception as e:
        return None, (f"Failed to reach Radarr: {e}", 500)


def get_radarr_ui_base():
    """
    Return the configured Radarr UI base using RADARR_HOST.
    Example:
      RADARR_HOST = tower-tail00b9.ts.net
      RADARR_API  = http://192.168.1.200:7878/api/v3
    Result:
      http://tower-tail00b9.ts.net:7878
    """
    api = urlparse(Config.RADARR_API)
    scheme = api.scheme
    port = api.port or 7878
    base = (Config.RADARR_HOST or api.hostname).strip("/")
    status, _ = fetch_status()
    url_base = (status or {}).get("urlBase", "") or ""
    return f"{scheme}://{base}:{port}{url_base}"


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@radarr_bp.route("/api/radarr/status")
def status():
    """Quick Radarr health check."""
    data, err = fetch_status()
    if err:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    return jsonify(
        {
            "ok": True,
            "name": data.get("appName", "Radarr"),
            "version": data.get("version"),
            "url": get_radarr_ui_base(),
            "urlBase": data.get("urlBase", ""),
        }
    )


@radarr_bp.route("/api/radarr/recent")
def recent():
    """Return recently added movies (cached 10 min)."""
    now = time.time()
    if _cache_recent["data"] and now - _cache_recent["timestamp"] < _CACHE_TTL:
        return jsonify(_cache_recent["data"])

    api_url = Config.RADARR_API.rstrip("/")
    api_key = Config.RADARR_KEY
    if not api_url or not api_key:
        return jsonify({"error": "Radarr not configured"}), 400

    try:
        r = requests.get(f"{api_url}/movie", headers={"X-Api-Key": api_key}, timeout=10)
        r.raise_for_status()
        movies = r.json()
    except Exception as e:
        return jsonify({"error": f"Failed to reach Radarr: {e}"}), 500

    movies = sorted(movies, key=lambda m: m.get("added", ""), reverse=True)
    ui_base = get_radarr_ui_base()

    recent = []
    for m in movies[:10]:
        # Poster
        img = ""
        for i in m.get("images", []):
            if i.get("coverType") == "poster":
                path = i.get("remoteUrl") or i.get("url")
                if path:
                    img = path if path.startswith("http") else f"{ui_base}{path}"
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
            f"{ui_base}/movie/{tmdb_id or radarr_id}"
            if (tmdb_id or radarr_id)
            else None
        )
        tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}" if tmdb_id else None
        imdb_url = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else None
        trakt_url = f"https://trakt.tv/movies/{imdb_id}" if imdb_id else None

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
                "trakt": trakt_url,
            }
        )

    _cache_recent["timestamp"] = now
    _cache_recent["data"] = recent
    return jsonify(recent)


@radarr_bp.route("/api/radarr/refresh", methods=["POST"])
def refresh_cache():
    """Manually clear Radarr poster cache."""
    global _cache_recent
    _cache_recent = {"timestamp": 0, "data": None}
    return jsonify({"status": "cleared"})
