from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class SourceBase(BaseModel):
    name: str
    type: str
    config: dict[str, Any]
    enabled: bool = True


class SourceCreate(SourceBase):
    pass


class SourceOut(SourceBase):
    id: int

    class Config:
        orm_mode = True


class NewsOut(BaseModel):
    id: int
    source: str
    url: str
    title: str
    summary: Optional[str]
    content: Optional[str]
    published_at: Optional[datetime]
    fetched_at: datetime
    language: Optional[str]
    analysis: Optional[dict[str, Any]]


class AnalysisOut(BaseModel):
    id: int
    news_item_id: int
    impacted_symbols: List[str]
    direction: str
    confidence: int
    horizon: str
    rationale: List[str]
    tags: List[str]
    created_at: datetime
    entities: List[str]
    topics: List[str]
    scoring: dict[str, Any]


class AlertCreate(BaseModel):
    name: str
    rule: dict[str, Any]
    enabled: bool = True


class AlertOut(AlertCreate):
    id: int
    created_at: datetime


class AlertEventOut(BaseModel):
    id: int
    alert_id: int
    news_item_id: int
    triggered_at: datetime
    payload: dict[str, Any]
