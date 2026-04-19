from __future__ import annotations

import time

from flask import current_app, jsonify

from . import bp


def _display():
    return current_app.config["PIBOARD_DISPLAY"]


def _news():
    return current_app.config["PIBOARD_NEWS"]


def _settings():
    return current_app.config["PIBOARD_SETTINGS"]


@bp.get("/api/status")
def api_status():
    display = _display()
    news = _news()
    settings = _settings()

    # Display state
    display_info = {
        "backend": display.backend_label(),
        "running": display.is_running(),
    }

    # News cache state per feed (no network call — only reads cache files)
    news_info = {}
    for feed_key in news.get_feed_keys():
        cached = news._load_cache(feed_key)
        if cached is None:
            news_info[feed_key] = {"cached": False}
        else:
            age_seconds = int(time.time() - cached.fetched_at)
            news_info[feed_key] = {
                "cached": True,
                "stale": cached.is_stale(news.cache_max_age_seconds),
                "article_count": len(cached.articles),
                "age_seconds": age_seconds,
            }

    return jsonify(
        {
            "display": display_info,
            "news": news_info,
            "settings": {
                "display_backend": settings.display_backend,
                "rotate_degrees_clockwise": settings.rotate_degrees_clockwise,
                "fit_mode": settings.fit_mode,
                "slideshow_delay_seconds": settings.slideshow_delay_seconds,
            },
        }
    )
