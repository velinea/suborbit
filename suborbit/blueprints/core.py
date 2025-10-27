from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    current_app,
)
import threading, time, json, os
from pathlib import Path
from ..suborbit_core import main_process, log, LOG_PATH, request_stop, get_tmdb_genres
from datetime import datetime, timezone

core_bp = Blueprint("core", __name__)

process_thread = None


def parse_genres(raw: str):
    include, exclude = [], []
    for g in [s.strip().lower() for s in raw.split(",") if s.strip()]:
        if g.startswith("!"):
            exclude.append(g[1:])
        else:
            include.append(g)
    return include or None, exclude or None


@core_bp.route("/")
def index():
    cfg = current_app.config
    return render_template(
        "index.html",
        start_year=cfg["START_YEAR"],
        end_year=cfg["END_YEAR"],
        min_tmdb=cfg["MIN_TMDB_RATING"],
        min_imdb=cfg["MIN_IMDB_RATING"],
        min_rt=cfg["MIN_RT_SCORE"],
        max_movies=cfg["MAX_MOVIES_PER_RUN"],
        max_pages=cfg["MAX_DISCOVER_PAGES"],
        min_vote_count=cfg["MIN_VOTE_COUNT"],
        subtitle_lang=cfg["SUBTITLE_LANG"],
        default_genres=cfg["DEFAULT_GENRES"],
        running=(process_thread and process_thread.is_alive()),
    )


@core_bp.route("/start", methods=["POST"])
def start():
    """Start the discovery process asynchronously."""
    if core_service.is_running():  # if you already track running jobs
        return jsonify({"status": "already_running"}), 400

    # Example: extract form fields if you need them
    form = request.form.to_dict()
    print("Starting discovery with form:", form)

    # Run discovery in background thread (so response returns fast)
    def run_discovery():
        try:
            core_service.run(form)  # your actual logic here
        except Exception as e:
            print("Discovery error:", e)

    threading.Thread(target=run_discovery, daemon=True).start()

    # Return immediate JSON response (no reload)
    return jsonify({"status": "started"})


@core_bp.route("/stop", methods=["POST"])
def stop():
    """Stop the running discovery."""
    stopped = core_service.stop()
    if stopped:
        return jsonify({"status": "stopped"})
    return jsonify({"status": "not_running"}), 400


@core_bp.route("/status")
def status():
    return jsonify({"running": (process_thread and process_thread.is_alive())})


@core_bp.route("/genres")
def genres():
    return jsonify(get_tmdb_genres())


@core_bp.route("/logs")
def logs():
    if LOG_PATH.exists():
        with LOG_PATH.open("r", encoding="utf-8") as f:
            return jsonify(f.readlines()[-200:])
    return jsonify([])


@core_bp.route("/healthz")
def healthz():
    """Basic health check for container monitors."""
    return {"status": "ok", "message": "SubOrbit is healthy"}, 200


@core_bp.route("/version")
def version():
    """Return SubOrbit version for UI and health checks."""
    app_version = os.getenv("APP_VERSION", "dev")
    return {"version": app_version}, 200
