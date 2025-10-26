from flask import Blueprint, jsonify, request
import requests, time
from urllib.parse import urlparse
from ..config import Config

radarr_bp = Blueprint("radarr", __name__)

# Simple caches
_cache_recent = {"timestamp": 0, "data": None}
_cache_status = {"timestamp": 0, "data": None}
_CACHE_TTL = 600
_STATUS_TTL = 300


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
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


def compute_ui_base():
    """
    Build the correct Radarr UI base (for clickable poster/movie links).

    - SubOrbit always talks to Radarr using Config.RADARR_API (LAN)
    - Tailnet clients automatically get Radarr links using their own host/IP
    - Works for Tailnet IPs (100.x.x.x), Tailscale DNS (.ts.net), or IPv6 (fd7a:)
    """
    api = urlparse(Config.RADARR_API)
    scheme = api.scheme
    port = api.port or 7878

    # Try fetching Radarr /system/status (cached) to detect any custom urlBase (like /radarr)
    status, _ = fetch_status()
    url_base = (status or {}).get("urlBase", "") or ""

    # Detect connection type
    client_host = request.host.split(":")[0] if request.host else ""
    remote_ip = request.remote_addr or ""

    is_tailnet = (
        client_host.startswith("100.")
        or client_host.endswith(".ts.net")
        or remote_ip.startswith("100.")
        or remote_ip.startswith("fd7a:")  # IPv6 Tailnet range
    )

    if is_tailnet:
        # Prefer the host the client actually used in the request
        if client_host and (
            client_host.startswith("100.") or client_host.endswith(".ts.net")
        ):
            host_for_ui = client_host
        else:
            # Fall back to the remote IP if the Host header is local-only (e.g. "tower")
            host_for_ui = remote_ip
    else:
        # Regular LAN access
        host_for_ui = api.hostname

    # Compose final base URL (strip /api/*, append urlBase if any)
    return f"{scheme}://{host_for_ui}:{port}{url_base}"


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@radarr_bp.route("/api/radarr/status")
def status():
    """Quick health check and version info."""
    data, err = fetch_status()
    if err:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    return jsonify(
        {
            "ok": True,
            "name": data.get("appName", "Radarr"),
            "version": data.get("version"),
            "url": compute_ui_base(),
            "urlBase": data.get("urlBase", ""),
        }
    )


@radarr_bp.route("/api/radarr/recent")
def recent():
    """Return recently added movies from Radarr (cached 10 min)."""
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
    ui_base = compute_ui_base()

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

    _cache_recent["timestamp"] = now
    _cache_recent["data"] = recent
    return jsonify(recent)


@radarr_bp.route("/api/radarr/refresh", methods=["POST"])
def refresh_cache():
    """Manually clear Radarr poster cache."""
    global _cache_recent
    _cache_recent = {"timestamp": 0, "data": None}
    return jsonify({"status": "cleared"})
