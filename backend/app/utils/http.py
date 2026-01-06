from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import requests
from cachetools import TTLCache


@dataclass
class RateLimiter:
    min_interval: float

    def __post_init__(self) -> None:
        self._last_call = 0.0

    def wait(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.time()


class CachedSession:
    def __init__(self, ttl_seconds: int = 300, maxsize: int = 512) -> None:
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self.session = requests.Session()

    def get(self, url: str, timeout: int = 10, **kwargs) -> requests.Response:
        if url in self.cache:
            return self.cache[url]
        response = self.session.get(url, timeout=timeout, **kwargs)
        self.cache[url] = response
        return response


class RetrySession:
    def __init__(self, retries: int = 3, backoff: float = 1.5) -> None:
        self.retries = retries
        self.backoff = backoff
        self.session = requests.Session()

    def get(self, url: str, timeout: int = 10, **kwargs) -> requests.Response:
        last_error: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                response = self.session.get(url, timeout=timeout, **kwargs)
                response.raise_for_status()
                return response
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(self.backoff ** attempt)
        if last_error:
            raise last_error
        raise RuntimeError("Request failed without exception")
