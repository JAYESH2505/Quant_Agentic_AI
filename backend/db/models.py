from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
    Text, Enum, Index
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class SignalType(str, enum.Enum):
    buy = "buy"
    sell = "sell"
    neutral = "neutral"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ── Core Tables ────────────────────────────────────────────────

class Asset(Base):
    __tablename__ = "assets"

    id         = Column(Integer, primary_key=True)
    ticker     = Column(String(20), unique=True, nullable=False, index=True)
    name       = Column(String(200))
    sector     = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("AgentRun", back_populates="asset")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id           = Column(Integer, primary_key=True)
    asset_id     = Column(Integer, ForeignKey("assets.id"), nullable=False)
    status       = Column(Enum(RunStatus), default=RunStatus.pending)
    started_at   = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error        = Column(Text, nullable=True)

    asset                  = relationship("Asset", back_populates="runs")
    ohlcv_data             = relationship("OHLCVData", back_populates="run")
    technical_signals      = relationship("TechnicalSignal", back_populates="run")
    fundamental_snapshot   = relationship("FundamentalSnapshot", back_populates="run", uselist=False)
    news_articles          = relationship("NewsArticle", back_populates="run")
    macro_indicators       = relationship("MacroIndicator", back_populates="run", uselist=False)
    analysis_report        = relationship("AnalysisReport", back_populates="run", uselist=False)

    __table_args__ = (Index("ix_agent_runs_asset_id", "asset_id"),)


class OHLCVData(Base):
    __tablename__ = "ohlcv_data"

    id       = Column(Integer, primary_key=True)
    run_id   = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    date     = Column(DateTime, nullable=False)
    open     = Column(Float)
    high     = Column(Float)
    low      = Column(Float)
    close    = Column(Float)
    volume   = Column(Float)

    run = relationship("AgentRun", back_populates="ohlcv_data")

    __table_args__ = (
        Index("ix_ohlcv_asset_date", "asset_id", "date"),
        Index("ix_ohlcv_run_id", "run_id"),
    )


class TechnicalSignal(Base):
    __tablename__ = "technical_signals"

    id             = Column(Integer, primary_key=True)
    run_id         = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    indicator      = Column(String(50), nullable=False)
    signal         = Column(Enum(SignalType), nullable=False)
    strength       = Column(Float)   # 0–100
    value          = Column(Float)
    interpretation = Column(Text)

    run = relationship("AgentRun", back_populates="technical_signals")

    __table_args__ = (Index("ix_technical_signals_run_id", "run_id"),)


class FundamentalSnapshot(Base):
    __tablename__ = "fundamental_snapshots"

    id                = Column(Integer, primary_key=True)
    run_id            = Column(Integer, ForeignKey("agent_runs.id"), nullable=False, unique=True)
    pe_ratio          = Column(Float, nullable=True)
    eps               = Column(Float, nullable=True)
    revenue_growth    = Column(Float, nullable=True)
    earnings_surprise = Column(Float, nullable=True)
    sentiment_score   = Column(Float, nullable=True)

    run = relationship("AgentRun", back_populates="fundamental_snapshot")


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id              = Column(Integer, primary_key=True)
    run_id          = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    title           = Column(Text)
    source          = Column(String(100))
    published_at    = Column(DateTime, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    url             = Column(Text, nullable=True)

    run = relationship("AgentRun", back_populates="news_articles")

    __table_args__ = (Index("ix_news_articles_run_id", "run_id"),)


class MacroIndicator(Base):
    __tablename__ = "macro_indicators"

    id            = Column(Integer, primary_key=True)
    run_id        = Column(Integer, ForeignKey("agent_runs.id"), nullable=False, unique=True)
    gdp_growth    = Column(Float, nullable=True)
    cpi           = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    fetched_at    = Column(DateTime, default=datetime.utcnow)

    run = relationship("AgentRun", back_populates="macro_indicators")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id                = Column(Integer, primary_key=True)
    run_id            = Column(Integer, ForeignKey("agent_runs.id"), nullable=False, unique=True)
    technical_bias    = Column(Enum(SignalType), nullable=True)
    fundamental_bias  = Column(Enum(SignalType), nullable=True)
    overall_bias      = Column(Enum(SignalType), nullable=True)
    narrative         = Column(Text, nullable=True)
    pdf_path          = Column(Text, nullable=True)
    created_at        = Column(DateTime, default=datetime.utcnow)

    run = relationship("AgentRun", back_populates="analysis_report")