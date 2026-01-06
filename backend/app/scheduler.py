from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from apscheduler.schedulers.background import BackgroundScheduler

from .analysis.engine import analyze_item
from .db import SessionLocal
from .models import Analysis, Alert, AlertEvent, NewsItem, Source
from .sources.demo import DemoReplay
from .sources.html import HtmlFetcher
from .sources.rss import fetch_rss
from .sse import event_hub
from .utils.dedupe import compute_dedupe, is_duplicate

SOURCE_STATUS: Dict[int, Dict[str, Any]] = {}


def _load_demo() -> DemoReplay:
    data_path = Path(__file__).parent / "demo_data.json"
    return DemoReplay(data_path)


def fetch_sources() -> None:
    session = SessionLocal()
    demo_mode = False
    demo = None
    try:
        sources = session.query(Source).filter(Source.enabled.is_(True)).all()
        existing_urls = [item.url for item in session.query(NewsItem.url).all()]
        existing_hashes = [item.hash for item in session.query(NewsItem.hash).all()]
        existing_titles = [item.title for item in session.query(NewsItem.title).all()]

        for source in sources:
            config = json.loads(source.config_json)
            items: List[dict[str, Any]] = []
            status = {"last_fetch": datetime.utcnow().isoformat(), "ok": True, "error": None}
            try:
                if source.type == "rss":
                    items = fetch_rss(config["url"])
                elif source.type == "html":
                    fetcher = HtmlFetcher(min_interval=config.get("min_interval", 2.0))
                    items = fetcher.fetch(config["url"])
                elif source.type == "demo":
                    demo_mode = True
                    if demo is None:
                        demo = _load_demo()
                    items = demo.next_batch(batch_size=1)
                else:
                    status["ok"] = False
                    status["error"] = "Unknown source type"
            except Exception as exc:  # noqa: BLE001
                status["ok"] = False
                status["error"] = str(exc)

            SOURCE_STATUS[source.id] = status

            for item in items:
                title = item.get("title", "")
                summary = item.get("summary", "")
                content = item.get("content", "")
                url = item.get("url", "")
                published_at = item.get("published_at")
                if isinstance(published_at, str):
                    try:
                        published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    except ValueError:
                        published_at = None

                dedupe_result = compute_dedupe(title, content, existing_titles, url)
                if is_duplicate(dedupe_result, existing_urls, existing_hashes):
                    continue

                news = NewsItem(
                    source_id=source.id,
                    url=dedupe_result.canonical_url,
                    title=title,
                    summary=summary,
                    content=content,
                    published_at=published_at,
                    fetched_at=datetime.utcnow(),
                    hash=dedupe_result.hash_value,
                    language=None,
                )
                session.add(news)
                session.flush()

                analysis = analyze_item(title, summary, content)
                news.language = analysis.scoring.get("language")
                analysis_row = Analysis(
                    news_item_id=news.id,
                    impacted_symbols_json=json.dumps(analysis.impacted_symbols),
                    direction=analysis.direction,
                    confidence=analysis.confidence,
                    horizon=analysis.horizon,
                    rationale_json=json.dumps(analysis.rationale),
                    tags_json=json.dumps(analysis.tags),
                    entities_json=json.dumps(analysis.entities),
                    topics_json=json.dumps(analysis.topics),
                    scoring_json=json.dumps(analysis.scoring),
                )
                session.add(analysis_row)
                session.flush()

                _evaluate_alerts(session, news.id, analysis)

                payload = {
                    "id": news.id,
                    "source": source.name,
                    "url": news.url,
                    "title": news.title,
                    "summary": news.summary,
                    "published_at": news.published_at.isoformat() if news.published_at else None,
                    "fetched_at": news.fetched_at.isoformat(),
                    "language": news.language,
                    "analysis": {
                        "impacted_symbols": analysis.impacted_symbols,
                        "direction": analysis.direction,
                        "confidence": analysis.confidence,
                        "horizon": analysis.horizon,
                        "rationale": analysis.rationale,
                        "tags": analysis.tags,
                        "entities": analysis.entities,
                        "topics": analysis.topics,
                        "scoring": analysis.scoring,
                    },
                }
                session.commit()
                existing_urls.append(news.url)
                existing_hashes.append(news.hash)
                existing_titles.append(news.title)
                try:
                    import asyncio

                    asyncio.run(event_hub.publish(payload))
                except RuntimeError:
                    pass
    finally:
        session.close()


def _evaluate_alerts(session: SessionLocal, news_item_id: int, analysis: Any) -> None:
    alerts = session.query(Alert).filter(Alert.enabled.is_(True)).all()
    for alert in alerts:
        rule = json.loads(alert.rule_json)
        symbol = rule.get("symbol")
        min_confidence = rule.get("min_confidence", 0)
        direction = rule.get("direction")
        if symbol and symbol not in analysis.impacted_symbols:
            continue
        if analysis.confidence < min_confidence:
            continue
        if direction and analysis.direction != direction:
            continue
        recent_event = (
            session.query(AlertEvent)
            .filter(AlertEvent.alert_id == alert.id)
            .order_by(AlertEvent.triggered_at.desc())
            .first()
        )
        if recent_event and (datetime.utcnow() - recent_event.triggered_at).total_seconds() < 600:
            continue
        event = AlertEvent(
            alert_id=alert.id,
            news_item_id=news_item_id,
            payload_json=json.dumps({
                "news_item_id": news_item_id,
                "analysis": {
                    "impacted_symbols": analysis.impacted_symbols,
                    "direction": analysis.direction,
                    "confidence": analysis.confidence,
                },
            }),
        )
        session.add(event)


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_sources, "interval", seconds=60, id="fetch_sources")
    scheduler.start()
    return scheduler
