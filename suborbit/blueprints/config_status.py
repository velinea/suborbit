from flask import Blueprint, jsonify
from ..config import Config
import requests, time, os, json

config_status_bp = Blueprint("config_status", __name__)

_cache = {"timestamp": 0, "data": None}
_CACHE_TTL = 300  # 5 minutes


@config_status_bp.route("/api/config/status")
def config_status():
    """Return SubOrbit system info: version + integration health."""
    now = time.time()
    if _cache["data"] and now - _cache["timestamp"] < _CACHE_TTL:
        return jsonify(_cache["data"])

    # --- Base info ---
    version = os.getenv("APP_VERSION", "dev")
    build_date = os.getenv("BUILD_DATE", "unknown")

    data = {
        "suborbit": {
            "ok": True,
            "version": version,
            "build": build_date,
            "details": "Core service running",
        },
        "radarr": {"ok": False, "details": "Not configured"},
        "trakt": {"ok": False, "details": "Not configured"},
        "opensubtitles": {"ok": False, "details": "Not configured"},
        "summary": "",
    }

    # --- Radarr check ---
    try:
        if Config.RADARR_API and Config.RADARR_KEY:
            url = f"{Config.RADARR_API.rstrip('/')}/system/status"
            r = requests.get(url, headers={"X-Api-Key": Config.RADARR_KEY}, timeout=5)
            r.raise_for_status()
            info = r.json()
            data["radarr"] = {
                "ok": True,
                "version": info.get("version"),
                "details": f"{info.get('appName', 'Radarr')} {info.get('version', '')}",
                "urlBase": info.get("urlBase", ""),
            }
        elif Config.RADARR_API:
            data["radarr"]["details"] = "Missing API key"
        else:
            data["radarr"]["details"] = "Missing API URL"
    except Exception as e:
        data["radarr"] = {"ok": False, "details": f"Error: {str(e)}"}

    # --- Trakt check ---
    try:
        if getattr(Config, "TRAKT_CLIENT_ID", None):
            data["trakt"] = {"ok": True, "details": "Configured"}
        else:
            data["trakt"]["details"] = "Missing TRAKT_CLIENT_ID"
    except Exception as e:
        data["trakt"] = {"ok": False, "details": str(e)}

    # --- OpenSubtitles check ---
    try:
        if getattr(Config, "OPENSUBTITLES_API_KEY", None):
            data["opensubtitles"] = {"ok": True, "details": "Configured"}
        else:
            data["opensubtitles"]["details"] = "Missing API key"
    except Exception as e:
        data["opensubtitles"] = {"ok": False, "details": str(e)}

    # --- Summary line ---
    ok_count = sum(1 for k, v in data.items() if isinstance(v, dict) and v.get("ok"))
    data["summary"] = f"{ok_count}/4 integrations ready"

    _cache["timestamp"] = now
    _cache["data"] = data
    return jsonify(data)
