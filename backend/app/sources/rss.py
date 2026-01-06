from __future__ import annotations

from datetime import datetime
from typing import Any, List

import feedparser

from ..utils.text import clean_text


def fetch_rss(url: str) -> List[dict[str, Any]]:
    feed = feedparser.parse(url)
    items: List[dict[str, Any]] = []
    for entry in feed.entries:
        published = None
        if getattr(entry, "published_parsed", None):
            published = datetime(*entry.published_parsed[:6])
        item = {
            "title": clean_text(entry.get("title", "")),
            "summary": clean_text(entry.get("summary", "")),
            "url": entry.get("link", ""),
            "published_at": published,
            "content": clean_text(entry.get("summary", "")),
        }
        items.append(item)
    return items
