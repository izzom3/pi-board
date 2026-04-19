"""NewsData.io API client with file-based caching.

Free tier: 200 credits/day, 30 credits per 15 min, 10 results per request.
We cache aggressively and refresh only when cache is stale.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Default categories with their NewsData.io query params
# Using country=us,gb,ca,au to focus on English-speaking western countries
DEFAULT_FEEDS: dict[str, dict[str, str]] = {
    "technology": {
        "label": "Technology",
        # Consumer tech: AI, gadgets, big tech companies, programming
        "q": "AI OR iPhone OR Google OR Apple OR Microsoft OR ChatGPT OR tech",
        "category": "technology",
        "language": "en",
        "country": "us,gb,ca,au",
        "prioritydomain": "top",
    },
    "gaming": {
        "label": "Gaming",
        # Video games only - no category filter to avoid entertainment/film bleeding in
        "q": "video game OR PlayStation OR Xbox OR Nintendo OR PC gaming OR Elden Ring OR GTA",
        "language": "en",
        "country": "us,gb,ca,au",
        "prioritydomain": "top",
    },
    "us": {
        "label": "US News",
        # Major US stories - top headlines, politics
        "category": "top,politics",
        "language": "en",
        "country": "us",
        "prioritydomain": "top",
    },
    "mlb": {
        "label": "MLB",
        # Major League Baseball news
        "q": "MLB OR \"Major League Baseball\" OR Yankees OR Dodgers OR baseball",
        "category": "sports",
        "language": "en",
        "country": "us",
        "prioritydomain": "top",
    },
    "film": {
        "label": "Film & TV",
        # Movies and television - reviews, releases, industry
        "q": "movie OR film OR television OR Netflix OR HBO OR Disney OR streaming OR box office",
        "category": "entertainment",
        "language": "en",
        "country": "us,gb,ca,au",
        "prioritydomain": "top",
    },
}

NEWSDATA_BASE_URL = "https://newsdata.io/api/1/latest"


@dataclass
class Article:
    article_id: str
    title: str
    description: str | None
    content: str | None
    link: str
    image_url: str | None
    source_name: str | None
    pub_date: str | None
    category: list[str] | None = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Article:
        return cls(
            article_id=data.get("article_id", ""),
            title=data.get("title") or "(No title)",
            description=data.get("description"),
            content=data.get("content"),
            link=data.get("link", ""),
            image_url=data.get("image_url"),
            source_name=data.get("source_name"),
            pub_date=data.get("pubDate"),
            category=data.get("category") or [],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "link": self.link,
            "image_url": self.image_url,
            "source_name": self.source_name,
            "pub_date": self.pub_date,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Article:
        return cls(**data)


@dataclass
class CachedFeed:
    feed_key: str
    articles: list[Article]
    next_page: str | None
    fetched_at: float  # Unix timestamp

    def is_stale(self, max_age_seconds: int) -> bool:
        return (time.time() - self.fetched_at) > max_age_seconds


class NewsService:
    def __init__(
        self,
        api_key: str,
        cache_dir: Path,
        cache_max_age_seconds: int = 1800,  # 30 min default
        feeds: dict[str, dict[str, str]] | None = None,
    ):
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.cache_max_age_seconds = cache_max_age_seconds
        self.feeds = feeds if feeds is not None else DEFAULT_FEEDS.copy()

        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, feed_key: str, page: str | None = None) -> Path:
        suffix = f"-{page}" if page else ""
        return self.cache_dir / f"feed-{feed_key}{suffix}.json"

    def _load_cache(self, feed_key: str, page: str | None = None) -> CachedFeed | None:
        path = self._cache_path(feed_key, page)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            articles = [Article.from_dict(a) for a in data.get("articles", [])]
            return CachedFeed(
                feed_key=data["feed_key"],
                articles=articles,
                next_page=data.get("next_page"),
                fetched_at=data.get("fetched_at", 0),
            )
        except Exception as exc:
            logger.warning("Failed to load cache for %s page=%s: %s", feed_key, page, exc)
            return None

    def _save_cache(self, feed: CachedFeed, page: str | None = None) -> None:
        path = self._cache_path(feed.feed_key, page)
        data = {
            "feed_key": feed.feed_key,
            "articles": [a.to_dict() for a in feed.articles],
            "next_page": feed.next_page,
            "fetched_at": feed.fetched_at,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _fetch_from_api(
        self, feed_key: str, page: str | None = None
    ) -> tuple[list[Article], str | None]:
        """Fetch articles from NewsData.io. Returns (articles, next_page_token)."""
        if not self.api_key:
            return [], None

        feed_config = self.feeds.get(feed_key, {})
        params: dict[str, str] = {"apikey": self.api_key}

        # Add feed-specific params
        for key in ("q", "qInTitle", "category", "country", "language", "prioritydomain"):
            if key in feed_config:
                params[key] = feed_config[key]

        # English default
        if "language" not in params:
            params["language"] = "en"

        # Pagination
        if page:
            params["page"] = page

        # Remove duplicates; respect per-feed prioritydomain, default to "medium"
        params["removeduplicate"] = "1"
        params.setdefault("prioritydomain", "medium")

        try:
            resp = requests.get(NEWSDATA_BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("API request failed for feed %s: %s", feed_key, exc)
            return [], None

        if data.get("status") != "success":
            logger.warning(
                "API returned non-success status for feed %s: %s", feed_key, data.get("status")
            )
            return [], None

        results = data.get("results") or []
        articles = [Article.from_api(r) for r in results]
        next_page = data.get("nextPage")

        return articles, next_page

    def get_feed(
        self, feed_key: str, page: str | None = None, force_refresh: bool = False
    ) -> CachedFeed:
        """Get articles for a feed, using cache when possible."""
        cached = self._load_cache(feed_key, page)

        if cached and not force_refresh and not cached.is_stale(self.cache_max_age_seconds):
            logger.debug("Cache hit for feed %s page=%s", feed_key, page)
            return cached

        logger.debug("Fetching fresh data for feed %s page=%s", feed_key, page)
        articles, next_page = self._fetch_from_api(feed_key, page)

        if not articles and cached:
            logger.info("API returned no articles for %s, using stale cache", feed_key)
            return cached

        feed = CachedFeed(
            feed_key=feed_key,
            articles=articles,
            next_page=next_page,
            fetched_at=time.time(),
        )
        self._save_cache(feed, page)
        return feed

    def get_article(self, article_id: str) -> Article | None:
        """Find an article by ID in any cached feed."""
        for cache_file in self.cache_dir.glob("feed-*.json"):
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                for a in data.get("articles", []):
                    if a.get("article_id") == article_id:
                        return Article.from_dict(a)
            except Exception as exc:
                logger.debug("Skipping cache file %s: %s", cache_file, exc)
                continue
        return None

    def get_all_feeds_summary(self, force_refresh: bool = False) -> dict[str, CachedFeed]:
        """Get first page of all configured feeds."""
        result = {}
        for feed_key in self.feeds:
            result[feed_key] = self.get_feed(feed_key, force_refresh=force_refresh)
        return result

    def get_feed_label(self, feed_key: str) -> str:
        return self.feeds.get(feed_key, {}).get("label", feed_key.title())

    def get_feed_keys(self) -> list[str]:
        return list(self.feeds.keys())
