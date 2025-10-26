from flask import Flask
from .config import Config

# Import blueprints
from .blueprints.core import core_bp
from .blueprints.trakt import trakt_bp
from .blueprints.radarr import radarr_bp
from .blueprints.config_status import config_status_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Register all blueprints
    app.register_blueprint(core_bp)
    app.register_blueprint(trakt_bp)
    app.register_blueprint(radarr_bp)
    app.register_blueprint(config_status_bp)

    return app
