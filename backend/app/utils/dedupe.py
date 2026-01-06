from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from rapidfuzz import fuzz

from .text import canonicalize_url, content_hash, clean_text


@dataclass
class DedupeResult:
    canonical_url: str
    hash_value: str
    title_similarity: int


def compute_dedupe(title: str, content: str, existing_titles: Iterable[str], url: str) -> DedupeResult:
    canonical_url = canonicalize_url(url)
    hash_value = content_hash(clean_text(f"{title} {content}"))
    similarity = 0
    for other in existing_titles:
        similarity = max(similarity, int(fuzz.ratio(title, other)))
    return DedupeResult(canonical_url=canonical_url, hash_value=hash_value, title_similarity=similarity)


def is_duplicate(result: DedupeResult, existing_urls: List[str], existing_hashes: List[str]) -> bool:
    if result.canonical_url in existing_urls:
        return True
    if result.hash_value in existing_hashes:
        return True
    if result.title_similarity >= 92:
        return True
    return False
