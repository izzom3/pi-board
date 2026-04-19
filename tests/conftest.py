from __future__ import annotations

import pytest


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("PIBOARD_DISPLAY_BACKEND", "dummy")
    monkeypatch.setenv("PIBOARD_POSTERS_DIR", str(tmp_path / "posters"))
    monkeypatch.setenv("PIBOARD_STATE_DIR", str(tmp_path / ".piboard"))
    monkeypatch.setenv("PIBOARD_NEWSDATA_API_KEY", "")
    monkeypatch.setenv("PIBOARD_ROTATE_DEGREES_CLOCKWISE", "0")
    monkeypatch.setenv("PIBOARD_SCREEN_WIDTH", "1920")
    monkeypatch.setenv("PIBOARD_SCREEN_HEIGHT", "1080")

    from pi_board.web import create_app

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
