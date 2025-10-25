from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    current_app,
)
import threading, time, json
from pathlib import Path
from ..suborbit_core import main_process, log, LOG_PATH, request_stop, get_tmdb_genres

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
    global process_thread
    cfg = current_app.config

    if process_thread and process_thread.is_alive():
        return redirect(url_for("core.index"))

    # Read submitted form data
    form = request.form
    args = {
        "start_year": int(form.get("start_year", cfg["START_YEAR"])),
        "end_year": int(form.get("end_year", cfg["END_YEAR"])),
        "min_tmdb": float(form.get("min_tmdb", cfg["MIN_TMDB_RATING"])),
        "min_imdb": float(form.get("min_imdb", cfg["MIN_IMDB_RATING"])),
        "min_rt": int(form.get("min_rt", cfg["MIN_RT_SCORE"])),
        "max_movies": int(form.get("max_movies", cfg["MAX_MOVIES_PER_RUN"])),
        "max_pages": int(form.get("max_pages", cfg["MAX_DISCOVER_PAGES"])),
        "subtitle_lang": form.get("subtitle_lang", cfg["SUBTITLE_LANG"]),
        "min_vote_count": int(form.get("min_vote_count", cfg["MIN_VOTE_COUNT"])),
        "randomize": bool(form.get("randomize")),
        "trakt_user": form.get("trakt_user", "").strip() or None,
        "trakt_list": form.get("trakt_list", "").strip() or None,
    }

    include, exclude = parse_genres(form.get("genres", ""))

    def run_process():
        main_process(include_genres=include, exclude_genres=exclude, **args)

    process_thread = threading.Thread(target=run_process, daemon=True)
    process_thread.start()
    time.sleep(1)

    return redirect(url_for("core.index"))


@core_bp.route("/stop", methods=["POST"])
def stop():
    request_stop()
    return redirect(url_for("core.index"))


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
