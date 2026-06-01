import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def _fetch_fred_series(series_id: str, limit: int = 1) -> float | None:
    """
    Fetch the latest value of a FRED series.
    """
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY not set in environment")

    params = {
        "series_id":     series_id,
        "api_key":       FRED_API_KEY,
        "file_type":     "json",
        "sort_order":    "desc",
        "limit":         limit,
    }

    response = requests.get(FRED_BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    observations = data.get("observations", [])
    for obs in observations:
        try:
            return float(obs["value"])
        except (ValueError, KeyError):
            continue
    return None


def fetch_macro_data() -> dict:
    """
    Fetch GDP growth, CPI, and Federal Funds Rate from FRED.
    Returns a dict ready for MacroIndicator DB insertion.
    """
    gdp_growth    = _fetch_fred_series("A191RL1Q225SBEA")  # Real GDP growth rate (%)
    cpi           = _fetch_fred_series("CPIAUCSL")          # CPI index
    interest_rate = _fetch_fred_series("FEDFUNDS")          # Federal Funds Rate (%)

    return {
        "gdp_growth":    gdp_growth,
        "cpi":           cpi,
        "interest_rate": interest_rate,
        "fetched_at":    datetime.utcnow(),
    }


def score_fundamental_bias(news: dict, earnings: dict, macro: dict) -> dict:
    """
    Combine news sentiment, earnings data, and macro indicators
    into an overall fundamental bias score and signal.
    """
    scores = []
    data_points = []

    # News sentiment (-1 to 1, scale to -100 to 100)
    sentiment = news.get("sentiment_score", 0)
    scores.append(sentiment * 100)
    data_points.append(f"News sentiment: {sentiment:+.2f}")

    # Earnings surprise
    surprise = earnings.get("earnings_surprise")
    if surprise is not None:
        scores.append(min(max(surprise, -100), 100))
        data_points.append(f"Earnings surprise: {surprise:+.1f}%")

    # P/E ratio (simple heuristic: below 20 = bullish, above 30 = bearish)
    pe = earnings.get("pe_ratio")
    if pe is not None:
        if pe < 20:
            scores.append(40)
            data_points.append(f"P/E ratio {pe:.1f} — below avg (bullish)")
        elif pe > 30:
            scores.append(-40)
            data_points.append(f"P/E ratio {pe:.1f} — above avg (bearish)")
        else:
            scores.append(0)
            data_points.append(f"P/E ratio {pe:.1f} — fair value")

    # Revenue growth
    rev_growth = earnings.get("revenue_growth")
    if rev_growth is not None:
        scores.append(min(max(rev_growth, -100), 100))
        data_points.append(f"Revenue growth: {rev_growth:+.1f}% YoY")

    # GDP growth
    gdp = macro.get("gdp_growth")
    if gdp is not None:
        if gdp > 2:
            scores.append(30)
            data_points.append(f"GDP growth {gdp:.1f}% — healthy macro")
        elif gdp < 0:
            scores.append(-50)
            data_points.append(f"GDP growth {gdp:.1f}% — recession territory")
        else:
            scores.append(0)
            data_points.append(f"GDP growth {gdp:.1f}% — slow growth")

    # CPI / Inflation (above 4% = bearish)
    cpi = macro.get("cpi")
    if cpi is not None:
        # FRED CPI is an index level, not a rate — skip scoring, include as context
        data_points.append(f"CPI index: {cpi:.1f}")

    # Interest rate (above 4% = bearish pressure)
    rate = macro.get("interest_rate")
    if rate is not None:
        if rate > 4:
            scores.append(-30)
            data_points.append(f"Fed Funds Rate {rate:.2f}% — restrictive (bearish)")
        elif rate < 2:
            scores.append(30)
            data_points.append(f"Fed Funds Rate {rate:.2f}% — accommodative (bullish)")
        else:
            scores.append(0)
            data_points.append(f"Fed Funds Rate {rate:.2f}% — neutral")

    # Aggregate
    avg_score = sum(scores) / len(scores) if scores else 0

    if avg_score > 20:
        bias = "buy"
    elif avg_score < -20:
        bias = "sell"
    else:
        bias = "neutral"

    return {
        "bias":        bias,
        "score":       round(avg_score, 1),
        "data_points": data_points,
    }