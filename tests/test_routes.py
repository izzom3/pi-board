from __future__ import annotations

import io
from pathlib import Path


def test_home_empty(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Pi-Board" in r.data


def test_placeholder_todo(client):
    r = client.get("/apps/todo")
    assert r.status_code == 200


def test_placeholder_unknown_redirects(client):
    r = client.get("/apps/unknown")
    assert r.status_code == 302


def test_upload_invalid_extension(client):
    data = {"file": (io.BytesIO(b"data"), "evil.gif")}
    r = client.post("/posters/upload", data=data, content_type="multipart/form-data")
    # Redirects back home (invalid extension)
    assert r.status_code == 302


def test_upload_and_delete(client, app):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buf, format="PNG")
    buf.seek(0)

    r = client.post(
        "/posters/upload",
        data={"file": (buf, "test.png")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 302

    posters_dir: Path = app.config["PIBOARD_POSTERS_DIR"]
    uploaded = list(posters_dir.glob("*.png"))
    assert len(uploaded) == 1
    name = uploaded[0].name

    r2 = client.post("/api/posters/delete", json={"filename": name})
    assert r2.status_code == 200
    assert r2.get_json()["status"] == "deleted"
    assert not uploaded[0].exists()


def test_delete_missing_returns_200(client):
    r = client.post("/api/posters/delete", json={"filename": "nope.png"})
    assert r.status_code == 200


def test_delete_traversal_blocked(client):
    r = client.post("/api/posters/delete", json={"filename": "../etc/passwd"})
    assert r.status_code == 400


def test_display_stop(client):
    r = client.post("/api/display/stop")
    assert r.status_code == 200
    assert r.get_json()["status"] == "stopped"


def test_display_start_random_empty(client):
    r = client.post("/api/display/start", json={"mode": "random"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "started"
    assert data["count"] == 0


def test_display_start_invalid_mode(client):
    r = client.post("/api/display/start", json={"mode": "bogus"})
    assert r.status_code == 400


def test_display_start_single_missing_poster(client):
    r = client.post("/api/display/start", json={"mode": "single", "poster": "ghost.png"})
    assert r.status_code == 404


def test_display_start_playlist_no_posters(client):
    r = client.post("/api/display/start", json={"mode": "playlist", "posters": []})
    assert r.status_code == 400


def test_news_home(client):
    r = client.get("/news")
    assert r.status_code == 200


def test_news_feed(client):
    r = client.get("/news/feed/technology")
    assert r.status_code == 200


def test_news_feed_unknown_redirects(client):
    r = client.get("/news/feed/notareal")
    assert r.status_code == 302


def test_news_display(client):
    r = client.get("/news/display/technology")
    assert r.status_code == 200


def test_news_refresh_all(client):
    r = client.post("/api/news/refresh", json={})
    assert r.status_code == 200


def test_news_refresh_unknown_feed(client):
    r = client.post("/api/news/refresh", json={"feed_key": "notareal"})
    assert r.status_code == 400


def test_api_status(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.get_json()
    assert "display" in data
    assert "news" in data
    assert "settings" in data
    assert data["display"]["backend"] == "dummy"
