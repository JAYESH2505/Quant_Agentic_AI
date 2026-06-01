import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")


def _score_sentiment(text: str) -> float:
    """
    Simple keyword-based sentiment scorer.
    Returns a float between -1.0 (bearish) and 1.0 (bullish).
    """
    bullish_keywords = [
        "surge", "soar", "rally", "beat", "record", "growth", "profit",
        "upgrade", "bullish", "outperform", "strong", "gain", "rise",
        "exceed", "positive", "buy", "upside", "breakthrough"
    ]
    bearish_keywords = [
        "crash", "plunge", "fall", "miss", "loss", "decline", "downgrade",
        "bearish", "underperform", "weak", "drop", "cut", "risk", "concern",
        "negative", "sell", "downside", "layoff", "recall", "lawsuit"
    ]

    text_lower = text.lower()
    bull_count = sum(1 for w in bullish_keywords if w in text_lower)
    bear_count = sum(1 for w in bearish_keywords if w in text_lower)
    total = bull_count + bear_count

    if total == 0:
        return 0.0
    return round((bull_count - bear_count) / total, 3)


def fetch_news_sentiment(ticker: str, days_back: int = 7) -> dict:
    """
    Fetch recent news articles for a ticker and score their sentiment.
    Returns articles list and an aggregate sentiment score.
    """
    if not NEWSAPI_KEY:
        raise ValueError("NEWSAPI_KEY not set in environment")

    from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q":        ticker,
        "from":     from_date,
        "sortBy":   "relevancy",
        "language": "en",
        "pageSize": 20,
        "apiKey":   NEWSAPI_KEY,
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    articles = []
    scores = []

    for item in data.get("articles", []):
        title   = item.get("title") or ""
        content = item.get("description") or ""
        text    = f"{title} {content}"
        score   = _score_sentiment(text)
        scores.append(score)

        published_at = None
        try:
            published_at = datetime.strptime(
                item["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
            )
        except Exception:
            pass

        articles.append({
            "title":           title,
            "source":          item.get("source", {}).get("name"),
            "published_at":    published_at,
            "sentiment_score": score,
            "url":             item.get("url"),
        })

    aggregate_score = round(sum(scores) / len(scores), 3) if scores else 0.0

    return {
        "articles":        articles,
        "sentiment_score": aggregate_score,
        "article_count":   len(articles),
    }