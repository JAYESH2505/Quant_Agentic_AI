from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _build_prompt(technical_signals: list[dict], technical_bias: str,
                  fundamental: dict, fundamental_bias: dict) -> str:

    tech_lines = []
    for s in technical_signals:
        tech_lines.append(
            f"  - {s['indicator']}: {s['signal'].upper()} "
            f"(strength: {s['strength']}/100) — {s['interpretation']}"
        )
    tech_block = "\n".join(tech_lines)

    fund_lines = "\n".join(
        f"  - {point}" for point in fundamental_bias.get("data_points", [])
    )

    prompt = f"""You are a quantitative research analyst. Below is structured data from a dual-sided stock analysis. Write a professional 3–4 paragraph research note based on this data.

---

TECHNICAL ANALYSIS
Overall technical bias: {technical_bias.upper()}

Indicator signals:
{tech_block}

---

FUNDAMENTAL ANALYSIS
Overall fundamental bias: {fundamental_bias['bias'].upper()} (score: {fundamental_bias['score']}/100)

Data points:
{fund_lines}

Supporting fundamentals:
  - P/E Ratio: {fundamental.get('pe_ratio', 'N/A')}
  - EPS: {fundamental.get('eps', 'N/A')}
  - Revenue Growth (YoY): {fundamental.get('revenue_growth', 'N/A')}%
  - Earnings Surprise: {fundamental.get('earnings_surprise', 'N/A')}%
  - News Sentiment Score: {fundamental.get('sentiment_score', 'N/A')} (range: -1 to +1)

---

TASK
Write a research note with exactly 4 paragraphs:

1. Technical signals: What the indicators are saying. Where they agree or conflict with each other.
2. Fundamental picture: What the earnings, macro, and sentiment data suggest about the company and macro environment.
3. Agreement or divergence: Where the technical and fundamental sides align or contradict each other.
4. Overall bias and reasoning: State a clear directional bias (e.g. cautiously bullish, strongly bearish, neutral with upside risk) and explain why.

Be direct, analytical, and concise. Do not use bullet points. Write in flowing paragraphs like a real research note.
"""
    return prompt


def _compute_technical_bias(signals: list[dict]) -> str:
    buy_score  = 0.0
    sell_score = 0.0
    total      = 0.0

    for s in signals:
        if s["indicator"] == "ATR":
            continue
        strength = s.get("strength", 50) or 50
        if s["signal"] == "buy":
            buy_score  += strength
        elif s["signal"] == "sell":
            sell_score += strength
        total += strength

    if total == 0:
        return "neutral"

    buy_pct  = buy_score  / total
    sell_pct = sell_score / total

    if buy_pct > 0.55:
        return "buy"
    elif sell_pct > 0.55:
        return "sell"
    else:
        return "neutral"


def synthesize_report(
    technical_signals: list[dict],
    fundamental: dict,
    fundamental_bias: dict
) -> dict:
    technical_bias = _compute_technical_bias(technical_signals)

    prompt = _build_prompt(
        technical_signals=technical_signals,
        technical_bias=technical_bias,
        fundamental=fundamental,
        fundamental_bias=fundamental_bias,
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": "You are a quantitative research analyst. Be direct, analytical, and professional."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    narrative = response.choices[0].message.content.strip()

    bias_map   = {"buy": 1, "neutral": 0, "sell": -1}
    tech_score = bias_map.get(technical_bias, 0)
    fund_score = bias_map.get(fundamental_bias["bias"], 0)
    combined   = tech_score + fund_score

    if combined >= 1:
        overall_bias = "buy"
    elif combined <= -1:
        overall_bias = "sell"
    else:
        overall_bias = "neutral"

    return {
        "technical_bias":   technical_bias,
        "fundamental_bias": fundamental_bias["bias"],
        "overall_bias":     overall_bias,
        "narrative":        narrative,
    }