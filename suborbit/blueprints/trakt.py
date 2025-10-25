from flask import Blueprint, jsonify
import requests, threading, time, os, json
from pathlib import Path
from ..suborbit_core import log

trakt_bp = Blueprint("trakt", __name__, url_prefix="/trakt")
trakt_state = {"state": "idle"}


@trakt_bp.route("/device")
def trakt_device():
    trakt_state["state"] = "waiting"
    url = "https://api.trakt.tv/oauth/device/code"
    headers = {"Content-Type": "application/json"}
    data = {"client_id": os.getenv("TRAKT_CLIENT_ID")}

    r = requests.post(url, json=data, headers=headers)
    device_info = r.json()

    def poll_for_token():
        token_url = "https://api.trakt.tv/oauth/device/token"
        payload = {
            "client_id": os.getenv("TRAKT_CLIENT_ID"),
            "client_secret": os.getenv("TRAKT_CLIENT_SECRET"),
            "code": device_info["device_code"],
        }
        for _ in range(60):
            time.sleep(device_info.get("interval", 5))
            resp = requests.post(token_url, json=payload, headers=headers)
            if resp.status_code == 200:
                tokens = resp.json()
                with open("trakt_token.json", "w", encoding="utf-8") as f:
                    json.dump(tokens, f, indent=2)
                log("✅ Trakt authenticated successfully!")
                trakt_state["state"] = "done"
                return
        trakt_state["state"] = "error"
        log("⚠️ Trakt auth timed out.")

    threading.Thread(target=poll_for_token, daemon=True).start()
    return jsonify(device_info)


@trakt_bp.route("/status")
def trakt_status_route():
    token_file = Path("trakt_token.json")
    if not token_file.exists():
        return jsonify({"authenticated": False, "state": trakt_state["state"]})

    try:
        data = json.loads(token_file.read_text())
        if data.get("access_token"):
            return jsonify({"authenticated": True, "state": "done"})
    except Exception:
        pass
    return jsonify({"authenticated": False, "state": "error"})
