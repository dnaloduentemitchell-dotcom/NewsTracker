from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from langdetect import detect

from ..utils.text import clean_text

try:
    import spacy

    _NLP = spacy.blank("en")
except Exception:  # noqa: BLE001
    _NLP = None


SYMBOL_RULES = {
    "XAU/USD": ["gold", "xau", "bullion", "real yields", "inflation", "geopolitics"],
    "DXY": ["dollar index", "dxy", "usd strength"],
    "EUR/USD": ["eurusd", "euro", "ecb"],
    "USD/JPY": ["usdjpy", "yen", "boj"],
    "GBP/USD": ["gbpusd", "pound", "boe"],
    "WTI": ["wti", "crude", "oil"],
    "BTC": ["bitcoin", "btc", "crypto"],
}

TOPIC_RULES = {
    "Fed": ["federal reserve", "powell", "rate hike", "rate cut"],
    "CPI": ["cpi", "inflation", "price index"],
    "Geopolitics": ["war", "conflict", "sanctions"],
    "Risk-off": ["risk-off", "safe haven", "flight to safety"],
    "Real yields": ["real yields", "treasury", "yields"],
}


@dataclass
class AnalysisResult:
    impacted_symbols: List[str]
    direction: str
    confidence: int
    horizon: str
    rationale: List[str]
    tags: List[str]
    entities: List[str]
    topics: List[str]
    scoring: Dict[str, Any]


def _extract_entities(text: str) -> List[str]:
    if _NLP is None:
        tokens = {word.strip() for word in text.split() if word.istitle()}
        return sorted(tokens)
    doc = _NLP(text)
    return sorted({ent.text for ent in doc.ents})


def _match_rules(text: str, rules: Dict[str, List[str]]) -> List[str]:
    matches = []
    lowered = text.lower()
    for key, keywords in rules.items():
        if any(keyword in lowered for keyword in keywords):
            matches.append(key)
    return matches


def analyze_item(title: str, summary: str, content: str) -> AnalysisResult:
    combined = clean_text(f"{title} {summary} {content}")
    language = "unknown"
    try:
        language = detect(combined) if combined else "unknown"
    except Exception:  # noqa: BLE001
        language = "unknown"

    entities = _extract_entities(combined)
    topics = _match_rules(combined, TOPIC_RULES)
    impacted = _match_rules(combined, SYMBOL_RULES)

    direction = "uncertain"
    confidence = 40
    horizon = "intraday"
    scoring: Dict[str, Any] = {"rules": []}
    rationale = []

    lowered = combined.lower()
    if "risk-off" in lowered or "flight to safety" in lowered:
        if "XAU/USD" in impacted:
            direction = "bullish"
            confidence += 20
            rationale.append("Risk-off language suggests safe-haven bid for gold.")
            scoring["rules"].append("risk_off_gold")
    if "real yields" in lowered or "yields" in lowered:
        if "XAU/USD" in impacted:
            direction = "bearish" if "higher" in lowered else direction
            confidence += 15
            rationale.append("Real yield commentary influences gold pricing.")
            scoring["rules"].append("real_yields_gold")
    if "rate cut" in lowered or "dovish" in lowered:
        if "DXY" in impacted:
            direction = "bearish"
            confidence += 15
            rationale.append("Dovish policy tone weighs on USD.")
            scoring["rules"].append("dovish_usd")
    if "rate hike" in lowered or "hawkish" in lowered:
        if "DXY" in impacted:
            direction = "bullish"
            confidence += 15
            rationale.append("Hawkish policy tone supports USD.")
            scoring["rules"].append("hawkish_usd")
    if "geopolitics" in lowered or "conflict" in lowered:
        if "XAU/USD" in impacted:
            direction = "bullish"
            confidence += 10
            rationale.append("Geopolitical risk supports safe-haven demand.")
            scoring["rules"].append("geo_risk_gold")

    if not impacted:
        impacted = ["DXY"]
        rationale.append("Defaulted to USD index due to macro relevance.")

    if confidence >= 80:
        horizon = "immediate"
    elif confidence < 50:
        horizon = "multi-day"

    tags = topics

    confidence = max(0, min(100, confidence))

    return AnalysisResult(
        impacted_symbols=impacted,
        direction=direction,
        confidence=confidence,
        horizon=horizon,
        rationale=rationale,
        tags=tags,
        entities=entities,
        topics=topics,
        scoring={"language": language, **scoring},
    )
