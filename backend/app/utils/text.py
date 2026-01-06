from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qsl(parsed.query, keep_blank_values=True)
    filtered = [(k, v) for k, v in query if not k.lower().startswith("utm_")]
    new_query = urlencode(filtered)
    return urlunparse(parsed._replace(query=new_query, fragment=""))


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()
