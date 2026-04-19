from __future__ import annotations

from flask import current_app, jsonify, redirect, render_template, request, url_for

from . import bp


def _news():
    return current_app.config["PIBOARD_NEWS"]


def _settings():
    return current_app.config["PIBOARD_SETTINGS"]


@bp.get("/news")
def news_home():
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
