from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SignalType(str, Enum):
    buy = "buy"
    sell = "sell"
    neutral = "neutral"


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ── Asset ─────────────────────────────────────────────────────

class AssetBase(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetOut(AssetBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Agent Run ─────────────────────────────────────────────────

class AgentRunCreate(BaseModel):
    ticker: str

class AgentRunOut(BaseModel):
    id: int
    asset_id: int
    status: RunStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


# ── Technical Signal ──────────────────────────────────────────

class TechnicalSignalOut(BaseModel):
    id: int
    indicator: str
    signal: SignalType
    strength: float
    value: Optional[float] = None
    interpretation: Optional[str] = None

    class Config:
        from_attributes = True


# ── Fundamental Snapshot ──────────────────────────────────────

class FundamentalSnapshotOut(BaseModel):
    id: int
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_surprise: Optional[float] = None
    sentiment_score: Optional[float] = None

    class Config:
        from_attributes = True


# ── News Article ──────────────────────────────────────────────

class NewsArticleOut(BaseModel):
    id: int
    title: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    sentiment_score: Optional[float] = None
    url: Optional[str] = None

    class Config:
        from_attributes = True


# ── Macro Indicator ───────────────────────────────────────────

class MacroIndicatorOut(BaseModel):
    id: int
    gdp_growth: Optional[float] = None
    cpi: Optional[float] = None
    interest_rate: Optional[float] = None
    fetched_at: datetime

    class Config:
        from_attributes = True


# ── Analysis Report ───────────────────────────────────────────

class AnalysisReportOut(BaseModel):
    id: int
    technical_bias: Optional[SignalType] = None
    fundamental_bias: Optional[SignalType] = None
    overall_bias: Optional[SignalType] = None
    narrative: Optional[str] = None
    pdf_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Full Report (combined response for GET /report/{run_id}) ──

class FullReportOut(BaseModel):
    run: AgentRunOut
    asset: AssetOut
    technical_signals: List[TechnicalSignalOut] = []
    fundamental: Optional[FundamentalSnapshotOut] = None
    news: List[NewsArticleOut] = []
    macro: Optional[MacroIndicatorOut] = None
    report: Optional[AnalysisReportOut] = None