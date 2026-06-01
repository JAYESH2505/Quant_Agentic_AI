from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from db.database import get_db
from db import crud, schemas
from agent.graph import run_agent

router = APIRouter()


# ── POST /analyze/{ticker} ────────────────────────────────────

@router.post("/analyze/{ticker}", response_model=schemas.AgentRunOut)
def analyze(ticker: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    ticker = ticker.upper().strip()

    # Get or create asset
    asset = crud.get_or_create_asset(db, ticker=ticker)

    # Create a new run
    run = crud.create_agent_run(db, asset_id=asset.id)

    # Run agent in background so API returns immediately
    background_tasks.add_task(run_agent, ticker, run.id, asset.id)

    return run


# ── GET /report/{run_id} ──────────────────────────────────────

@router.get("/report/{run_id}", response_model=schemas.FullReportOut)
def get_report(run_id: int, db: Session = Depends(get_db)):
    report = crud.get_full_report(db, run_id)
    if not report:
        raise HTTPException(status_code=404, detail="Run not found")
    return report


# ── GET /signals/{ticker} ─────────────────────────────────────

@router.get("/signals/{ticker}")
def get_signals(ticker: str, db: Session = Depends(get_db)):
    ticker = ticker.upper().strip()
    asset  = db.query(crud.Asset).filter(crud.Asset.ticker == ticker).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Ticker not found")

    # Get latest completed run
    from db.models import AgentRun, RunStatus
    run = (
        db.query(AgentRun)
        .filter(AgentRun.asset_id == asset.id, AgentRun.status == RunStatus.completed)
        .order_by(AgentRun.started_at.desc())
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="No completed analysis found for this ticker")

    signals = crud.get_technical_signals(db, run.id)
    return {
        "ticker":   ticker,
        "run_id":   run.id,
        "signals":  [schemas.TechnicalSignalOut.from_orm(s) for s in signals],
    }


# ── GET /fundamentals/{ticker} ────────────────────────────────

@router.get("/fundamentals/{ticker}")
def get_fundamentals(ticker: str, db: Session = Depends(get_db)):
    ticker = ticker.upper().strip()
    asset  = db.query(crud.Asset).filter(crud.Asset.ticker == ticker).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Ticker not found")

    from db.models import AgentRun, RunStatus
    run = (
        db.query(AgentRun)
        .filter(AgentRun.asset_id == asset.id, AgentRun.status == RunStatus.completed)
        .order_by(AgentRun.started_at.desc())
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="No completed analysis found for this ticker")

    fundamental = crud.get_fundamental_snapshot(db, run.id)
    macro       = crud.get_macro_indicators(db, run.id)
    news        = crud.get_news_articles(db, run.id)

    return {
        "ticker":      ticker,
        "run_id":      run.id,
        "fundamental": schemas.FundamentalSnapshotOut.from_orm(fundamental) if fundamental else None,
        "macro":       schemas.MacroIndicatorOut.from_orm(macro) if macro else None,
        "news":        [schemas.NewsArticleOut.from_orm(a) for a in news],
    }


# ── GET /compare ──────────────────────────────────────────────

@router.get("/compare")
def compare(tickers: str, db: Session = Depends(get_db)):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if len(ticker_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 tickers")

    from db.models import AgentRun, RunStatus
    results = []

    for ticker in ticker_list:
        asset = db.query(crud.Asset).filter(crud.Asset.ticker == ticker).first()
        if not asset:
            results.append({"ticker": ticker, "error": "Not found"})
            continue

        run = (
            db.query(AgentRun)
            .filter(AgentRun.asset_id == asset.id, AgentRun.status == RunStatus.completed)
            .order_by(AgentRun.started_at.desc())
            .first()
        )
        if not run:
            results.append({"ticker": ticker, "error": "No completed analysis"})
            continue

        report  = crud.get_analysis_report(db, run.id)
        signals = crud.get_technical_signals(db, run.id)

        results.append({
            "ticker":           ticker,
            "run_id":           run.id,
            "overall_bias":     report.overall_bias if report else None,
            "technical_bias":   report.technical_bias if report else None,
            "fundamental_bias": report.fundamental_bias if report else None,
            "signal_count":     len(signals),
        })

    return {"comparison": results}


# ── GET /history ──────────────────────────────────────────────

@router.get("/history")
def get_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    runs = crud.get_all_runs(db, skip=skip, limit=limit)
    return {
        "total": len(runs),
        "runs": [
            {
                "run_id":       r.id,
                "ticker":       r.asset.ticker if r.asset else None,
                "status":       r.status,
                "started_at":   r.started_at,
                "completed_at": r.completed_at,
            }
            for r in runs
        ]
    }