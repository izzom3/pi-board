"""Convenience entrypoint.

The primary application lives under src/pi_board.
This wrapper keeps `python3 app.py` working.
"""

from pi_board.web import create_app

app = create_app()


if __name__ == "__main__":
    settings = app.config["PIBOARD_SETTINGS"]
    app.run(host=settings.host, port=settings.port, debug=True)
