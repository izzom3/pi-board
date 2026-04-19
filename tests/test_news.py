from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from pi_board.news import NewsService


def _make_service(tmp_path: Path, api_key: str = "test-key") -> NewsService:
    return NewsService(api_key=api_key, cache_dir=tmp_path / "cache")


def _write_cache(service: NewsService, feed_key: str, articles: list, fetched_at: float) -> None:
    path = service._cache_path(feed_key)
    data = {
        "feed_key": feed_key,
        "articles": articles,
        "next_page": None,
        "fetched_at": fetched_at,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _article_dict(n: int = 1) -> dict:
    return {
        "article_id": f"id-{n}",
        "title": f"Title {n}",
        "description": None,
        "content": None,
        "link": "https://example.com",
        "image_url": None,
        "source_name": "Test",
        "pub_date": None,
        "category": [],
    }


def test_cache_hit_returns_without_api_call(tmp_path: Path):
    service = _make_service(tmp_path)
    _write_cache(service, "technology", [_article_dict(1)], fetched_at=time.time())

    with patch("pi_board.news.requests.get") as mock_get:
        result = service.get_feed("technology")

    mock_get.assert_not_called()
    assert len(result.articles) == 1
    assert result.articles[0].article_id == "id-1"


def test_stale_cache_triggers_api_call(tmp_path: Path):
    service = _make_service(tmp_path)
    old_time = time.time() - 9999
    _write_cache(service, "technology", [_article_dict(1)], fetched_at=old_time)

    api_response = {
        "status": "success",
        "results": [
            {
                "article_id": "fresh-1",
                "title": "Fresh Article",
                "description": None,
                "content": None,
                "link": "https://example.com",
                "image_url": None,
                "source_name": "Test",
                "pubDate": None,
                "category": [],
            }
        ],
        "nextPage": None,
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = api_response
    mock_resp.raise_for_status.return_value = None

    with patch("pi_board.news.requests.get", return_value=mock_resp):
        result = service.get_feed("technology")

    assert result.articles[0].article_id == "fresh-1"


def test_api_failure_falls_back_to_stale_cache(tmp_path: Path):
    service = _make_service(tmp_path)
    old_time = time.time() - 9999
    _write_cache(service, "technology", [_article_dict(1)], fetched_at=old_time)

    with patch("pi_board.news.requests.get", side_effect=Exception("network error")):
        result = service.get_feed("technology")

    assert len(result.articles) == 1
    assert result.articles[0].article_id == "id-1"


def test_no_api_key_returns_empty(tmp_path: Path):
    service = _make_service(tmp_path, api_key="")
    result = service.get_feed("technology")
    assert result.articles == []


def test_prioritydomain_not_clobbered(tmp_path: Path):
    """Feed-level prioritydomain=top must survive into the API params."""
    service = _make_service(tmp_path)
    captured_params: dict = {}

    def fake_get(url, params, timeout):
        captured_params.update(params)
        raise Exception("stop here")

    with patch("pi_board.news.requests.get", side_effect=fake_get):
        service.get_feed("technology")

    assert captured_params.get("prioritydomain") == "top"


def test_prioritydomain_defaults_to_medium_when_not_set(tmp_path: Path):
    """Feeds without prioritydomain in their config should get 'medium' by default."""
    service = _make_service(tmp_path)
    # Inject a feed with no prioritydomain key
    service.feeds["noprio"] = {"label": "No Prio", "q": "test", "language": "en"}
    captured_params: dict = {}

    def fake_get(url, params, timeout):
        captured_params.update(params)
        raise Exception("stop here")

    with patch("pi_board.news.requests.get", side_effect=fake_get):
        service.get_feed("noprio")

    assert captured_params.get("prioritydomain") == "medium"


def test_force_refresh_bypasses_fresh_cache(tmp_path: Path):
    """force_refresh hits the API even when cache is fresh."""
    service = _make_service(tmp_path)
    _write_cache(service, "technology", [_article_dict(1)], fetched_at=time.time())

    fresh_article = {
        "article_id": "fresh-99",
        "title": "Fresh",
        "description": None,
        "content": None,
        "link": "https://example.com",
        "image_url": None,
        "source_name": "Test",
        "pubDate": None,
        "category": [],
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "status": "success",
        "results": [fresh_article],
        "nextPage": None,
    }
    mock_resp.raise_for_status.return_value = None

    with patch("pi_board.news.requests.get", return_value=mock_resp) as mock_get:
        result = service.get_feed("technology", force_refresh=True)

    mock_get.assert_called_once()
    assert result.articles[0].article_id == "fresh-99"


def test_get_article_finds_across_cache_files(tmp_path: Path):
    service = _make_service(tmp_path)
    _write_cache(service, "technology", [_article_dict(42)], fetched_at=time.time())
    _write_cache(service, "gaming", [_article_dict(99)], fetched_at=time.time())

    article = service.get_article("id-42")
    assert article is not None
    assert article.article_id == "id-42"

    missing = service.get_article("id-000")
    assert missing is None
