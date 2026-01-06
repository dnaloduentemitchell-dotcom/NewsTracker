from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .db import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    config_json = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)

    news_items = relationship("NewsItem", back_populates="source")


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    hash = Column(String, nullable=False)
    language = Column(String, nullable=True)

    source = relationship("Source", back_populates="news_items")
    analysis = relationship("Analysis", back_populates="news_item", uselist=False)


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    news_item_id = Column(Integer, ForeignKey("news_items.id"), nullable=False)
    impacted_symbols_json = Column(Text, nullable=False)
    direction = Column(String, nullable=False)
    confidence = Column(Integer, nullable=False)
    horizon = Column(String, nullable=False)
    rationale_json = Column(Text, nullable=False)
    tags_json = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    entities_json = Column(Text, nullable=True)
    topics_json = Column(Text, nullable=True)
    scoring_json = Column(Text, nullable=True)

    news_item = relationship("NewsItem", back_populates="analysis")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    rule_json = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    news_item_id = Column(Integer, ForeignKey("news_items.id"), nullable=False)
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    payload_json = Column(Text, nullable=False)
