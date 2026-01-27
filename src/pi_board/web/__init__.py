from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from pi_board.config import load_settings
from pi_board.display.manager import create_display_manager


def create_app() -> Flask:
    load_dotenv(override=False)
    settings = load_settings()

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config["PIBOARD_SETTINGS"] = settings
    app.config["PIBOARD_POSTERS_DIR"] = settings.posters_dir

    state_dir = Path(".piboard").resolve()
    app.config["PIBOARD_DISPLAY"] = create_display_manager(
        settings.display_backend,
        state_dir=state_dir,
    )

    settings.posters_dir.mkdir(parents=True, exist_ok=True)

    from .routes import bp

    app.register_blueprint(bp)
    return app
