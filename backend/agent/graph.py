from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from datetime import datetime

from agent.tools.market import fetch_ohlcv, fetch_earnings_data
from agent.tools.indicators import run_technical_indicators, score_technical_signals
from agent.tools.news import fetch_news_sentiment
from agent.tools.macro import fetch_macro_data, score_fundamental_bias
from agent.synthesizer import synthesize_report
from db.database import SessionLocal
from db import crud
from db.models import RunStatus


# ── State Schema ──────────────────────────────────────────────

class AgentState(TypedDict):
    ticker:             str
    run_id:             int
    asset_id:           int
    ohlcv:              Optional[dict]
    technical_signals:  Optional[list]
    earnings:           Optional[dict]
    news:               Optional[dict]
    macro:              Optional[dict]
    fundamental_bias:   Optional[dict]
    report:             Optional[dict]
    error:              Optional[str]


# ── Nodes ─────────────────────────────────────────────────────

def node_fetch_ohlcv(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        crud.update_run_status(db, state["run_id"], RunStatus.running)
        ohlcv = fetch_ohlcv(state["ticker"])
        crud.save_ohlcv(
            db,
            run_id=state["run_id"],
            asset_id=state["asset_id"],
            rows=[{k: v for k, v in row.items() if k != "df"}
                  for row in ohlcv["rows"]]
        )
        return {**state, "ohlcv": ohlcv}
    except Exception as e:
        return {**state, "error": f"fetch_ohlcv failed: {str(e)}"}
    finally:
        db.close()


def node_run_indicators(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    try:
        df = state["ohlcv"]["df"]
        raw_indicators = run_technical_indicators(df)
        signals = score_technical_signals(raw_indicators)

        db = SessionLocal()
        try:
            crud.save_technical_signals(db, state["run_id"], signals)
        finally:
            db.close()

        return {**state, "technical_signals": signals}
    except Exception as e:
        return {**state, "error": f"run_indicators failed: {str(e)}"}


def node_fetch_earnings(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    try:
        earnings = fetch_earnings_data(state["ticker"])
        return {**state, "earnings": earnings}
    except Exception as e:
        return {**state, "error": f"fetch_earnings failed: {str(e)}"}


def node_fetch_news(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    try:
        news = fetch_news_sentiment(state["ticker"])

        db = SessionLocal()
        try:
            crud.save_news_articles(db, state["run_id"], news["articles"])
        finally:
            db.close()

        return {**state, "news": news}
    except Exception as e:
        # News failure is non-fatal — continue with empty sentiment
        return {**state, "news": {"sentiment_score": 0.0, "articles": [], "article_count": 0}}


def node_fetch_macro(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    try:
        macro = fetch_macro_data()

        db = SessionLocal()
        try:
            crud.save_macro_indicators(db, state["run_id"], {
                "gdp_growth":    macro.get("gdp_growth"),
                "cpi":           macro.get("cpi"),
                "interest_rate": macro.get("interest_rate"),
                "fetched_at":    macro.get("fetched_at"),
            })
        finally:
            db.close()

        return {**state, "macro": macro}
    except Exception as e:
        return {**state, "macro": {"gdp_growth": None, "cpi": None, "interest_rate": None}}


def node_score_fundamentals(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    try:
        fundamental_bias = score_fundamental_bias(
            news=state["news"],
            earnings=state["earnings"],
            macro=state["macro"],
        )

        # Merge sentiment score into earnings dict for synthesizer
        earnings_with_sentiment = {
            **state["earnings"],
            "sentiment_score": state["news"].get("sentiment_score", 0.0),
        }

        db = SessionLocal()
        try:
            crud.save_fundamental_snapshot(db, state["run_id"], {
                "pe_ratio":          state["earnings"].get("pe_ratio"),
                "eps":               state["earnings"].get("eps"),
                "revenue_growth":    state["earnings"].get("revenue_growth"),
                "earnings_surprise": state["earnings"].get("earnings_surprise"),
                "sentiment_score":   state["news"].get("sentiment_score", 0.0),
            })
        finally:
            db.close()

        return {
            **state,
            "fundamental_bias": fundamental_bias,
            "earnings": earnings_with_sentiment,
        }
    except Exception as e:
        return {**state, "error": f"score_fundamentals failed: {str(e)}"}


def node_synthesize(state: AgentState) -> AgentState:
    if state.get("error"):
        return state
    try:
        report = synthesize_report(
            technical_signals=state["technical_signals"],
            fundamental=state["earnings"],
            fundamental_bias=state["fundamental_bias"],
        )

        db = SessionLocal()
        try:
            crud.save_analysis_report(db, state["run_id"], report)
            crud.update_run_status(db, state["run_id"], RunStatus.completed)
        finally:
            db.close()

        return {**state, "report": report}
    except Exception as e:
        return {**state, "error": f"synthesize failed: {str(e)}"}


def node_handle_error(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        crud.update_run_status(
            db, state["run_id"], RunStatus.failed, error=state.get("error")
        )
    finally:
        db.close()
    return state


# ── Routing ───────────────────────────────────────────────────

def should_continue(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    return "continue"


# ── Build Graph ───────────────────────────────────────────────

def build_agent() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("fetch_ohlcv",         node_fetch_ohlcv)
    graph.add_node("run_indicators",       node_run_indicators)
    graph.add_node("fetch_earnings",       node_fetch_earnings)
    graph.add_node("fetch_news",           node_fetch_news)
    graph.add_node("fetch_macro",          node_fetch_macro)
    graph.add_node("score_fundamentals",   node_score_fundamentals)
    graph.add_node("synthesize",           node_synthesize)
    graph.add_node("handle_error",         node_handle_error)

    # Entry point
    graph.set_entry_point("fetch_ohlcv")

    # Edges with error routing after each critical node
    graph.add_conditional_edges("fetch_ohlcv", should_continue, {
        "continue":     "run_indicators",
        "handle_error": "handle_error",
    })
    graph.add_conditional_edges("run_indicators", should_continue, {
        "continue":     "fetch_earnings",
        "handle_error": "handle_error",
    })

    # These three run sequentially but news/macro failures are non-fatal
    graph.add_edge("fetch_earnings",    "fetch_news")
    graph.add_edge("fetch_news",        "fetch_macro")
    graph.add_edge("fetch_macro",       "score_fundamentals")

    graph.add_conditional_edges("score_fundamentals", should_continue, {
        "continue":     "synthesize",
        "handle_error": "handle_error",
    })

    graph.add_edge("synthesize",    END)
    graph.add_edge("handle_error",  END)

    return graph.compile()


# Compiled agent — import this in routes
agent = build_agent()


# ── Runner ────────────────────────────────────────────────────

def run_agent(ticker: str, run_id: int, asset_id: int) -> dict:
    initial_state: AgentState = {
        "ticker":            ticker,
        "run_id":            run_id,
        "asset_id":          asset_id,
        "ohlcv":             None,
        "technical_signals": None,
        "earnings":          None,
        "news":              None,
        "macro":             None,
        "fundamental_bias":  None,
        "report":            None,
        "error":             None,
    }
    final_state = agent.invoke(initial_state)
    return final_state