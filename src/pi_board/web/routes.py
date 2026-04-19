from __future__ import annotations

import secrets
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from pi_board.posters import list_posters, safe_join_posters_dir

bp = Blueprint("piboard", __name__)


def _posters_dir() -> Path:
    return current_app.config["PIBOARD_POSTERS_DIR"]


def _display():
    return current_app.config["PIBOARD_DISPLAY"]


def _news():
    return current_app.config["PIBOARD_NEWS"]


def _settings():
    return current_app.config["PIBOARD_SETTINGS"]


@bp.get("/")
def home() -> str:
    posters = list_posters(_posters_dir())
    return render_template("posters.html", posters=posters)


@bp.get("/apps/<app_name>")
def placeholder_app(app_name: str):
    if app_name not in {"todo", "calendar"}:
        return redirect(url_for("piboard.home"))
    return render_template("placeholder.html", app_name=app_name)


@bp.get("/media/posters/<path:filename>")
def media_poster(filename: str):
    # send_from_directory protects against traversal, but we also keep allowed-extension constraints
    safe_join_posters_dir(_posters_dir(), filename)
    return send_from_directory(_posters_dir(), filename)


@bp.post("/posters/upload")
def posters_upload():
    if "file" not in request.files:
        return redirect(url_for("piboard.home"))

    file = request.files["file"]
    if not file or not file.filename:
        return redirect(url_for("piboard.home"))

    filename = Path(file.filename).name
    try:
        target = safe_join_posters_dir(_posters_dir(), filename)
    except ValueError:
        return redirect(url_for("piboard.home"))

    # avoid overwriting by default
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        filename = f"{stem}-{secrets.token_hex(3)}{suffix}"
        target = safe_join_posters_dir(_posters_dir(), filename)

    file.save(target)
    return redirect(url_for("piboard.home"))


@bp.post("/api/posters/delete")
def api_delete_poster():
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename is required"}), 400

    try:
        path = safe_join_posters_dir(_posters_dir(), filename)
    except ValueError:
        return jsonify({"error": "invalid filename"}), 400

    if path.exists():
        path.unlink()
    return jsonify({"status": "deleted", "filename": filename})


@bp.post("/api/display/stop")
def api_display_stop():
    _display().stop()
    return jsonify({"status": "stopped"})


@bp.post("/api/display/start")
def api_display_start():
    data = request.get_json(silent=True) or {}

    mode = (data.get("mode") or "random").strip().lower()
    delay = data.get("delay_seconds")
    shuffle = bool(data.get("shuffle", True))

    settings = current_app.config["PIBOARD_SETTINGS"]
    delay_seconds = (
        int(delay)
        if isinstance(delay, (int, float, str)) and str(delay).isdigit()
        else settings.slideshow_delay_seconds
    )

    posters = list_posters(_posters_dir())
    poster_paths = [(_posters_dir() / p) for p in posters]

    if mode == "random":
        import random

        random.shuffle(poster_paths)
        _display().start_slideshow(paths=poster_paths, delay_seconds=delay_seconds, shuffle=True)
        return jsonify({"status": "started", "mode": "random", "count": len(poster_paths)})

    if mode == "playlist":
        selected = data.get("posters") or []
        if not isinstance(selected, list) or not selected:
            return jsonify({"error": "posters list required"}), 400
        paths: list[Path] = []
        for name in selected:
            try:
                p = safe_join_posters_dir(_posters_dir(), str(name))
            except ValueError:
                continue
            if p.exists():
                paths.append(p)
        if not paths:
            return jsonify({"error": "no valid posters"}), 400
        _display().start_slideshow(paths=paths, delay_seconds=delay_seconds, shuffle=shuffle)
        return jsonify(
            {
                "status": "started",
                "mode": "playlist",
                "count": len(paths),
                "shuffle": shuffle,
            }
        )

    if mode == "single":
        filename = data.get("poster")
        if not filename:
            return jsonify({"error": "poster is required"}), 400
        try:
            path = safe_join_posters_dir(_posters_dir(), str(filename))
        except ValueError:
            return jsonify({"error": "invalid poster"}), 400
        if not path.exists():
            return jsonify({"error": "poster not found"}), 404
        _display().show_single(path)
        return jsonify({"status": "started", "mode": "single", "poster": path.name})

    return jsonify({"error": "invalid mode"}), 400


# ─────────────────────────────────────────────────────────────────────────────
# News routes
# ─────────────────────────────────────────────────────────────────────────────


@bp.get("/news")
def news_home():
    """News landing page: shows summary of all feeds."""
    news = _news()
    settings = _settings()
    feeds = news.get_all_feeds_summary()

    feed_data = []
    for key in news.get_feed_keys():
        feed = feeds.get(key)
        feed_data.append(
            {
                "key": key,
                "label": news.get_feed_label(key),
                "articles": feed.articles[:3] if feed else [],
            }
        )

    return render_template(
        "news/home.html",
        feeds=feed_data,
        rotate=settings.rotate_degrees_clockwise,
    )


@bp.get("/news/feed/<feed_key>")
def news_feed(feed_key: str):
    """Full feed page with all articles."""
    news = _news()
    settings = _settings()

    if feed_key not in news.get_feed_keys():
        return redirect(url_for("piboard.news_home"))

    page = request.args.get("page")
    feed = news.get_feed(feed_key, page=page)

    return render_template(
        "news/feed.html",
        feed_key=feed_key,
        feed_label=news.get_feed_label(feed_key),
        articles=feed.articles,
        next_page=feed.next_page,
        rotate=settings.rotate_degrees_clockwise,
    )


@bp.get("/news/article/<article_id>")
def news_article(article_id: str):
    """Single article view for reading."""
    news = _news()
    settings = _settings()
    article = news.get_article(article_id)

    if not article:
        return redirect(url_for("piboard.news_home"))

    return render_template(
        "news/article.html",
        article=article,
        rotate=settings.rotate_degrees_clockwise,
    )


@bp.get("/news/display/<feed_key>")
def news_display(feed_key: str):
    """Display mode: full-screen article slideshow for the rotated monitor."""
    news = _news()
    settings = _settings()

    if feed_key not in news.get_feed_keys():
        return redirect(url_for("piboard.news_home"))

    feed = news.get_feed(feed_key)
    index = request.args.get("index", "0")
    try:
        idx = int(index) % len(feed.articles) if feed.articles else 0
    except ValueError:
        idx = 0

    article = feed.articles[idx] if feed.articles else None
    total = len(feed.articles)

    return render_template(
        "news/display.html",
        feed_key=feed_key,
        feed_label=news.get_feed_label(feed_key),
        article=article,
        index=idx,
        total=total,
        rotate=settings.rotate_degrees_clockwise,
    )


@bp.post("/api/news/refresh")
def api_news_refresh():
    """Force refresh a specific feed or all feeds."""
    news = _news()
    data = request.get_json(silent=True) or {}
    feed_key = data.get("feed_key")

    if feed_key:
        if feed_key not in news.get_feed_keys():
            return jsonify({"error": "unknown feed"}), 400
        news.get_feed(feed_key, force_refresh=True)
        return jsonify({"status": "refreshed", "feed": feed_key})

    news.get_all_feeds_summary(force_refresh=True)
    return jsonify({"status": "refreshed", "feed": "all"})
