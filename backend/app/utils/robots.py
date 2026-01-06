from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from urllib.parse import urlparse

import robotexclusionrulesparser as rerp

from .http import RetrySession


@dataclass
class RobotsCache:
    user_agent: str = "NewsTrackerBot"

    def __post_init__(self) -> None:
        self._parsers: Dict[str, rerp.RobotExclusionRulesParser] = {}
        self._session = RetrySession()

    def allowed(self, url: str) -> bool:
        domain = urlparse(url).netloc
        if domain not in self._parsers:
            parser = rerp.RobotExclusionRulesParser()
            robots_url = f"https://{domain}/robots.txt"
            try:
                response = self._session.get(robots_url, timeout=5)
                parser.parse(response.text)
            except Exception:
                parser.parse("")
            self._parsers[domain] = parser
        return self._parsers[domain].is_allowed(self.user_agent, url)
