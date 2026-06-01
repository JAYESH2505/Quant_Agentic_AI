import yfinance as yf
import pandas as pd
from datetime import datetime


def fetch_ohlcv(ticker: str, period: str = "6mo") -> dict:
    """
    Fetch historical OHLCV data for a ticker.
    Returns a dict with metadata and a list of rows ready for DB insertion.
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)

    if df.empty:
        raise ValueError(f"No OHLCV data found for ticker: {ticker}")

    df = df.reset_index()
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    df.columns = ["date", "open", "high", "low", "close", "volume"]
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

    rows = df.to_dict(orient="records")

    return {
        "ticker": ticker,
        "period": period,
        "rows": rows,
        "df": df          # kept in memory for indicator computation
    }


def fetch_earnings_data(ticker: str) -> dict:
    """
    Fetch fundamental data: P/E, EPS, revenue growth, earnings surprise.
    Returns a flat dict ready for FundamentalSnapshot.
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    # Revenue growth (YoY) from financials
    revenue_growth = None
    try:
        financials = stock.financials
        if financials is not None and not financials.empty:
            revenues = financials.loc["Total Revenue"].dropna()
            if len(revenues) >= 2:
                revenue_growth = float(
                    (revenues.iloc[0] - revenues.iloc[1]) / abs(revenues.iloc[1]) * 100
                )
    except Exception:
        pass

    # Earnings surprise from earnings history
    earnings_surprise = None
    try:
        earnings = stock.earnings_history
        if earnings is not None and not earnings.empty:
            latest = earnings.iloc[0]
            if "epsEstimate" in latest and "epsActual" in latest:
                estimate = latest["epsEstimate"]
                actual = latest["epsActual"]
                if estimate and estimate != 0:
                    earnings_surprise = float((actual - estimate) / abs(estimate) * 100)
    except Exception:
        pass

    return {
        "pe_ratio":          info.get("trailingPE"),
        "eps":               info.get("trailingEps"),
        "revenue_growth":    revenue_growth,
        "earnings_surprise": earnings_surprise,
    }