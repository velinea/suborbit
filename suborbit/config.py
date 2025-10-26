import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env (default location: /config/.env inside container)
dotenv_path = Path("/config/.env")
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv()  # fallback to current dir


class Config:
    """Flask configuration class."""

    # ===== API KEYS =====
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
    OS_API_KEY = os.getenv("OS_API_KEY", "")
    OMDB_KEY = os.getenv("OMDB_KEY", "")
    TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID", "")
    TRAKT_CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET", "")
    RADARR_API = os.getenv("RADARR_API", "http://192.168.1.200:7878/api/v3")
    RADARR_KEY = os.getenv("RADARR_KEY", "")

    # ===== YEAR RANGE =====
    START_YEAR = int(os.getenv("START_YEAR", 2020))
    END_YEAR = int(os.getenv("END_YEAR", 2020))

    # ===== RATINGS =====
    MIN_TMDB_RATING = float(os.getenv("MIN_TMDB_RATING", 0))
    MIN_IMDB_RATING = float(os.getenv("MIN_IMDB_RATING", 0))
    MIN_RT_SCORE = int(os.getenv("MIN_RT_SCORE", 0))

    USE_TMDB = os.getenv("USE_TMDB", "true").lower() == "true"
    USE_IMDB = os.getenv("USE_IMDB", "true").lower() == "true"
    USE_RT = os.getenv("USE_RT", "true").lower() == "true"

    # ===== RADARR =====
    QUALITY_PROFILE_ID = int(os.getenv("QUALITY_PROFILE_ID", 1))
    ROOT_FOLDER = os.getenv("ROOT_FOLDER", "/movies")
    SEARCH_FOR_MOVIE = os.getenv("SEARCH_FOR_MOVIE", "false").lower() == "true"

    # ===== SCRIPT SETTINGS =====
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 5))  # unused if sequential
    QUIET_MODE = os.getenv("QUIET_MODE", "false").lower() == "true"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    MAX_MOVIES_PER_RUN = int(os.getenv("MAX_MOVIES_PER_RUN", 10))
    OS_DELAY = int(os.getenv("OS_DELAY", 3))  # seconds between OpenSubtitles calls
    RANDOM_SELECTION = os.getenv("RANDOM_SELECTION", "false").lower() == "true"

    # ===== EXTRA FILTERS =====
    MIN_VOTE_COUNT = int(os.getenv("MIN_VOTE_COUNT", 0))
    MAX_DISCOVER_PAGES = int(os.getenv("MAX_DISCOVER_PAGES", 3))  # TMDb pages to parse
    ALLOWED_LANGUAGES = [
        l.strip() for l in os.getenv("ALLOWED_LANGUAGES", "").split(",") if l.strip()
    ]
    SUBTITLE_LANG = os.getenv("SUBTITLE_LANG", "fi")
    DEFAULT_GENRES = os.getenv("ALLOWED_GENRES", "")
