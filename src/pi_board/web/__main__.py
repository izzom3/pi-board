from __future__ import annotations

from pi_board.web import create_app


def main() -> None:
    app = create_app()
    settings = app.config["PIBOARD_SETTINGS"]
    app.run(host=settings.host, port=settings.port, debug=True)


if __name__ == "__main__":
    main()
