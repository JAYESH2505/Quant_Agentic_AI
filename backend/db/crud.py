from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from db.models import (
    Asset, AgentRun, OHLCVData, TechnicalSignal,
    FundamentalSnapshot, NewsArticle, MacroIndicator, AnalysisReport,
    RunStatus
)


# ── Asset ─────────────────────────────────────────────────────

def get_or_create_asset(db: Session, ticker: str, name: str = None, sector: str = None) -> Asset:
    asset = db.query(Asset).filter(Asset.ticker == ticker).first()
    if not asset:
        asset = Asset(ticker=ticker, name=name, sector=sector)
        db.add(asset)
        db.commit()
        db.refresh(asset)
    return asset


# ── Agent Run ─────────────────────────────────────────────────

def create_agent_run(db: Session, asset_id: int) -> AgentRun:
    run = AgentRun(asset_id=asset_id, status=RunStatus.pending)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_agent_run(db: Session, run_id: int) -> Optional[AgentRun]:
    return db.query(AgentRun).filter(AgentRun.id == run_id).first()


def update_run_status(
    db: Session,
    run_id: int,
    status: RunStatus,
    error: str = None
) -> AgentRun:
    run = get_agent_run(db, run_id)
    run.status = status
    if status == RunStatus.completed or status == RunStatus.failed:
        run.completed_at = datetime.utcnow()
    if error:
        run.error = error
    db.commit()
    db.refresh(run)
    return run


def get_all_runs(db: Session, skip: int = 0, limit: int = 50):
    return (
        db.query(AgentRun)
        .order_by(AgentRun.started_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── OHLCV ─────────────────────────────────────────────────────

def save_ohlcv(db: Session, run_id: int, asset_id: int, rows: list[dict]):
    objects = [
        OHLCVData(run_id=run_id, asset_id=asset_id, **row)
        for row in rows
    ]
    db.bulk_save_objects(objects)
    db.commit()


# ── Technical Signals ─────────────────────────────────────────

def save_technical_signals(db: Session, run_id: int, signals: list[dict]):
    objects = [
        TechnicalSignal(run_id=run_id, **s)
        for s in signals
    ]
    db.bulk_save_objects(objects)
    db.commit()


def get_technical_signals(db: Session, run_id: int):
    return db.query(TechnicalSignal).filter(TechnicalSignal.run_id == run_id).all()


# ── Fundamental Snapshot ──────────────────────────────────────

def save_fundamental_snapshot(db: Session, run_id: int, data: dict) -> FundamentalSnapshot:
    snapshot = FundamentalSnapshot(run_id=run_id, **data)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_fundamental_snapshot(db: Session, run_id: int) -> Optional[FundamentalSnapshot]:
    return db.query(FundamentalSnapshot).filter(FundamentalSnapshot.run_id == run_id).first()


# ── News Articles ─────────────────────────────────────────────

def save_news_articles(db: Session, run_id: int, articles: list[dict]):
    objects = [
        NewsArticle(run_id=run_id, **a)
        for a in articles
    ]
    db.bulk_save_objects(objects)
    db.commit()


def get_news_articles(db: Session, run_id: int):
    return db.query(NewsArticle).filter(NewsArticle.run_id == run_id).all()


# ── Macro Indicators ──────────────────────────────────────────

def save_macro_indicators(db: Session, run_id: int, data: dict) -> MacroIndicator:
    macro = MacroIndicator(run_id=run_id, **data)
    db.add(macro)
    db.commit()
    db.refresh(macro)
    return macro


def get_macro_indicators(db: Session, run_id: int) -> Optional[MacroIndicator]:
    return db.query(MacroIndicator).filter(MacroIndicator.run_id == run_id).first()


# ── Analysis Report ───────────────────────────────────────────

def save_analysis_report(db: Session, run_id: int, data: dict) -> AnalysisReport:
    report = AnalysisReport(run_id=run_id, **data)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_analysis_report(db: Session, run_id: int) -> Optional[AnalysisReport]:
    return db.query(AnalysisReport).filter(AnalysisReport.run_id == run_id).first()


# ── Full Report (for GET /report/{run_id}) ────────────────────

def get_full_report(db: Session, run_id: int) -> Optional[dict]:
    run = get_agent_run(db, run_id)
    if not run:
        return None
    return {
        "run": run,
        "asset": run.asset,
        "technical_signals": get_technical_signals(db, run_id),
        "fundamental": get_fundamental_snapshot(db, run_id),
        "news": get_news_articles(db, run_id),
        "macro": get_macro_indicators(db, run_id),
        "report": get_analysis_report(db, run_id),
    }