from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .db import SessionLocal, init_db
from .models import Alert, AlertEvent, Analysis, NewsItem, Source
from .scheduler import SOURCE_STATUS, start_scheduler
from .schemas import (
    AlertCreate,
    AlertEventOut,
    AlertOut,
    NewsOut,
    SourceCreate,
    SourceOut,
)
from .sse import event_hub

app = FastAPI(title="Forex News Impact Tracker")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup() -> None:
    init_db()
    _seed_sources()
    start_scheduler()


@app.get("/api/news", response_model=List[NewsOut])
def list_news(
    symbol: Optional[str] = None,
    source: Optional[str] = None,
    min_confidence: int = 0,
    db: Session = Depends(get_db),
) -> List[NewsOut]:
    query = db.query(NewsItem).join(Source).outerjoin(Analysis)
    if source:
        query = query.filter(Source.name == source)
    items = query.order_by(NewsItem.fetched_at.desc()).limit(100).all()
    output = []
    for item in items:
        analysis = item.analysis
        if analysis and min_confidence and analysis.confidence < min_confidence:
            continue
        if analysis and symbol and symbol not in json.loads(analysis.impacted_symbols_json):
            continue
        output.append(_serialize_news(item))
    return output


@app.get("/api/news/{news_id}", response_model=NewsOut)
def get_news(news_id: int, db: Session = Depends(get_db)) -> NewsOut:
    item = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    return _serialize_news(item)


@app.get("/api/analysis/latest", response_model=List[NewsOut])
def latest_analysis(symbol: Optional[str] = None, db: Session = Depends(get_db)) -> List[NewsOut]:
    return list_news(symbol=symbol, db=db)


@app.get("/api/sources", response_model=List[SourceOut])
def list_sources(db: Session = Depends(get_db)) -> List[SourceOut]:
    sources = db.query(Source).all()
    output = []
    for source in sources:
        output.append(
            SourceOut(
                id=source.id,
                name=source.name,
                type=source.type,
                config=json.loads(source.config_json),
                enabled=source.enabled,
            )
        )
    return output


@app.post("/api/sources", response_model=SourceOut)
def upsert_source(payload: SourceCreate, db: Session = Depends(get_db)) -> SourceOut:
    source = db.query(Source).filter(Source.name == payload.name).first()
    if source is None:
        source = Source(
            name=payload.name,
            type=payload.type,
            config_json=json.dumps(payload.config),
            enabled=payload.enabled,
        )
        db.add(source)
    else:
        source.type = payload.type
        source.config_json = json.dumps(payload.config)
        source.enabled = payload.enabled
    db.commit()
    db.refresh(source)
    return SourceOut(
        id=source.id,
        name=source.name,
        type=source.type,
        config=json.loads(source.config_json),
        enabled=source.enabled,
    )


@app.post("/api/alerts", response_model=AlertOut)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)) -> AlertOut:
    alert = Alert(name=payload.name, rule_json=json.dumps(payload.rule), enabled=payload.enabled)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return AlertOut(id=alert.id, name=alert.name, rule=payload.rule, enabled=alert.enabled, created_at=alert.created_at)


@app.get("/api/alerts/history", response_model=List[AlertEventOut])
def alerts_history(db: Session = Depends(get_db)) -> List[AlertEventOut]:
    events = db.query(AlertEvent).order_by(AlertEvent.triggered_at.desc()).limit(100).all()
    output = []
    for event in events:
        output.append(
            AlertEventOut(
                id=event.id,
                alert_id=event.alert_id,
                news_item_id=event.news_item_id,
                triggered_at=event.triggered_at,
                payload=json.loads(event.payload_json),
            )
        )
    return output


@app.get("/api/sources/status")
def sources_status() -> dict[str, Any]:
    return SOURCE_STATUS


@app.get("/api/stream")
async def stream() -> StreamingResponse:
    return StreamingResponse(event_hub.subscribe(), media_type="text/event-stream")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


def _serialize_news(item: NewsItem) -> NewsOut:
    analysis = None
    if item.analysis:
        analysis = {
            "impacted_symbols": json.loads(item.analysis.impacted_symbols_json),
            "direction": item.analysis.direction,
            "confidence": item.analysis.confidence,
            "horizon": item.analysis.horizon,
            "rationale": json.loads(item.analysis.rationale_json),
            "tags": json.loads(item.analysis.tags_json),
            "entities": json.loads(item.analysis.entities_json or "[]"),
            "topics": json.loads(item.analysis.topics_json or "[]"),
            "scoring": json.loads(item.analysis.scoring_json or "{}"),
        }
    return NewsOut(
        id=item.id,
        source=item.source.name if item.source else "",
        url=item.url,
        title=item.title,
        summary=item.summary,
        content=item.content,
        published_at=item.published_at,
        fetched_at=item.fetched_at,
        language=item.language,
        analysis=analysis,
    )


def _seed_sources() -> None:
    session = SessionLocal()
    try:
        if session.query(Source).count() > 0:
            return
        defaults = [
            {
                "name": "Reuters FX RSS",
                "type": "rss",
                "config": {"url": "https://feeds.reuters.com/reuters/businessNews"},
            },
            {
                "name": "Federal Reserve RSS",
                "type": "rss",
                "config": {"url": "https://www.federalreserve.gov/feeds/press_all.xml"},
            },
            {
                "name": "ECB RSS",
                "type": "rss",
                "config": {"url": "https://www.ecb.europa.eu/rss/press.html"},
            },
            {
                "name": "Demo Replay",
                "type": "demo",
                "config": {},
            },
        ]
        for item in defaults:
            source = Source(
                name=item["name"],
                type=item["type"],
                config_json=json.dumps(item["config"]),
                enabled=True,
            )
            session.add(source)
        session.commit()
    finally:
        session.close()
