from flask import Flask, render_template, request, redirect, url_for, jsonify
import threading, time, os, json, requests
from pathlib import Path

from finsubs_core import (
    main_process,
    log,
    LOG_PATH,
    request_stop,
    reset_stop,
    get_tmdb_genres,
)
from config import (
    START_YEAR,
    END_YEAR,
    MIN_TMDB_RATING,
    MIN_IMDB_RATING,
    MIN_RT_SCORE,
    MAX_MOVIES_PER_RUN,
    MAX_DISCOVER_PAGES,
    MIN_VOTE_COUNT,
    SUBTITLE_LANG,
    TRAKT_CLIENT_ID,
    TRAKT_CLIENT_SECRET,
)


# ---- Genre parser ----
def parse_genres(raw: str):
    """Parse comma-separated string into include/exclude lists."""
    include, exclude = [], []
    for g in [s.strip().lower() for s in raw.split(",") if s.strip()]:
        if g.startswith("!"):
            exclude.append(g[1:])
        else:
            include.append(g)
    return include or None, exclude or None


app = Flask(__name__)
process_thread = None


@app.route("/")
def index():
    # No sticky values here (handled client-side via localStorage)
    return render_template(
        "index.html",
        start_year=START_YEAR,
        end_year=END_YEAR,
        min_tmdb=MIN_TMDB_RATING,
        min_imdb=MIN_IMDB_RATING,
        min_rt=MIN_RT_SCORE,
        max_movies=MAX_MOVIES_PER_RUN,
        max_pages=MAX_DISCOVER_PAGES,
        min_vote_count=MIN_VOTE_COUNT,
        subtitle_lang=SUBTITLE_LANG,
        running=(process_thread and process_thread.is_alive()),
    )


@app.route("/start", methods=["POST"])
def start():
    global process_thread
    if process_thread and process_thread.is_alive():
        return redirect(url_for("index"))

    # Read submitted values
    start_year = int(request.form.get("start_year", START_YEAR))
    end_year = int(request.form.get("end_year", END_YEAR))
    min_tmdb = float(request.form.get("min_tmdb", MIN_TMDB_RATING))
    min_imdb = float(request.form.get("min_imdb", MIN_IMDB_RATING))
    min_rt = int(request.form.get("min_rt", MIN_RT_SCORE))
    max_movies = int(request.form.get("max_movies", MAX_MOVIES_PER_RUN))
    max_pages = int(request.form.get("max_pages", MAX_DISCOVER_PAGES))
    subtitle_lang = request.form.get("subtitle_lang", SUBTITLE_LANG)
    min_vote_count = int(request.form.get("min_vote_count", MIN_VOTE_COUNT))
    randomize = bool(request.form.get("randomize"))
    trakt_user = request.form.get("trakt_user", "").strip()
    trakt_list = request.form.get("trakt_list", "").strip()

    # Parse genres
    raw_genres = request.form.get("genres", "")
    include_genres, exclude_genres = parse_genres(raw_genres)

    def run_process():
        main_process(
            start_year=start_year,
            end_year=end_year,
            include_genres=include_genres,
            exclude_genres=exclude_genres,
            min_tmdb=min_tmdb,
            min_imdb=min_imdb,
            min_rt=min_rt,
            max_movies=max_movies,
            min_vote_count=min_vote_count,
            subtitle_lang=subtitle_lang,
            randomize=randomize,
            max_pages=max_pages,
            trakt_user=trakt_user or None,
            trakt_list=trakt_list or None,
        )

    process_thread = threading.Thread(target=run_process, daemon=True)
    process_thread.start()
    time.sleep(1)

    return redirect(url_for("index"))


@app.route("/stop", methods=["POST"])
def stop():
    request_stop()
    return redirect(url_for("index"))


@app.route("/status")
def status():
    return jsonify({"running": (process_thread and process_thread.is_alive())})


@app.route("/genres")
def genres():
    return jsonify(get_tmdb_genres())


@app.route("/logs")
def logs():
    if LOG_PATH.exists():
        with LOG_PATH.open("r", encoding="utf-8") as f:
            lines = f.readlines()[-200:]
        return jsonify(lines)
    return jsonify([])


# -------------------------------------------------------------
# Trakt authentication flow
# -------------------------------------------------------------
trakt_state = {"state": "idle"}  # renamed variable


@app.route("/trakt/device")
def trakt_device():
    """Initiate Trakt device auth flow."""
    global trakt_state
    trakt_state = {"state": "waiting"}
    url = "https://api.trakt.tv/oauth/device/code"
    data = {"client_id": TRAKT_CLIENT_ID}
    headers = {"Content-Type": "application/json"}

    r = requests.post(url, json=data, headers=headers)
    device_info = r.json()

    # Poll for completion in background thread
    def poll_for_token():
        global trakt_state
        token_url = "https://api.trakt.tv/oauth/device/token"
        payload = {
            "client_id": TRAKT_CLIENT_ID,
            "client_secret": TRAKT_CLIENT_SECRET,
            "code": device_info["device_code"],
        }
        for _ in range(60):  # poll up to ~5 minutes
            time.sleep(device_info.get("interval", 5))
            resp = requests.post(token_url, json=payload, headers=headers)
            if resp.status_code == 200:
                tokens = resp.json()
                with open("trakt_token.json", "w", encoding="utf-8") as f:
                    json.dump(tokens, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                log("✅ Trakt authenticated successfully!")
                trakt_state = {"state": "done"}
                return
        log("⚠️ Trakt auth timed out.")
        trakt_state = {"state": "error"}

    threading.Thread(target=poll_for_token, daemon=True).start()

    return jsonify(device_info)


@app.route("/trakt/status")
def trakt_status_route():
    """Report whether Trakt authentication is active."""
    from pathlib import Path
    import json

    token_file = Path("trakt_token.json")
    if not token_file.exists():
        return jsonify(
            {"authenticated": False, "state": trakt_state.get("state", "idle")}
        )

    try:
        data = json.loads(token_file.read_text())
        access_token = data.get("access_token")
        if access_token:
            return jsonify(
                {"authenticated": True, "state": trakt_state.get("state", "done")}
            )
    except Exception:
        pass

    return jsonify({"authenticated": False, "state": trakt_state.get("state", "error")})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
