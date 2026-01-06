from __future__ import annotations

from datetime import datetime
from typing import Any, List

from bs4 import BeautifulSoup

from ..utils.http import CachedSession, RateLimiter, RetrySession
from ..utils.robots import RobotsCache
from ..utils.text import clean_text


class HtmlFetcher:
    def __init__(self, min_interval: float = 2.0) -> None:
        self.rate_limiter = RateLimiter(min_interval=min_interval)
        self.robots = RobotsCache()
        self.session = RetrySession()
        self.cache = CachedSession(ttl_seconds=600)

    def fetch(self, url: str) -> List[dict[str, Any]]:
        if not self.robots.allowed(url):
            return []
        self.rate_limiter.wait()
        response = self.cache.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.text if soup.title else ""
        summary = soup.get_text(" ")[:500]
        return [
            {
                "title": clean_text(title),
                "summary": clean_text(summary),
                "url": url,
                "published_at": None,
                "content": clean_text(summary),
                "fetched_at": datetime.utcnow(),
            }
        ]
