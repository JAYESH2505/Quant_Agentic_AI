import pandas as pd
import numpy as np


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


def _bollinger_bands(series: pd.Series, period=20, std_dev=2):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper, sma, lower


def run_technical_indicators(df: pd.DataFrame) -> dict:
    """
    Run all indicators on the OHLCV dataframe.
    Returns a dict of indicator name -> raw values (last row).
    """
    close = df["close"]
    volume = df["volume"]

    # RSI
    rsi_series = _rsi(close)
    rsi_value = float(rsi_series.iloc[-1])

    # MACD
    macd_line, signal_line = _macd(close)
    macd_value = float(macd_line.iloc[-1])
    macd_signal = float(signal_line.iloc[-1])

    # Bollinger Bands
    bb_upper, bb_mid, bb_lower = _bollinger_bands(close)
    bb_upper_val = float(bb_upper.iloc[-1])
    bb_lower_val = float(bb_lower.iloc[-1])
    current_price = float(close.iloc[-1])

    # MA Crossover (50/200)
    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1])

    # Volume Profile (simple: compare last 5 days avg vs 20 days avg)
    vol_5 = float(volume.rolling(5).mean().iloc[-1])
    vol_20 = float(volume.rolling(20).mean().iloc[-1])

    # ATR
    df = df.copy()
    df["prev_close"] = close.shift(1)
    df["tr"] = df[["high", "prev_close"]].max(axis=1) - df[["low", "prev_close"]].min(axis=1)
    atr_value = float(df["tr"].rolling(14).mean().iloc[-1])

    return {
        "rsi":        {"value": rsi_value, "macd_signal": None},
        "macd":       {"value": macd_value, "signal_line": macd_signal},
        "bbands":     {"upper": bb_upper_val, "lower": bb_lower_val, "price": current_price},
        "ma_cross":   {"ma50": ma50, "ma200": ma200},
        "volume":     {"vol_5": vol_5, "vol_20": vol_20},
        "atr":        {"value": atr_value, "price": current_price},
    }


def score_technical_signals(indicators: dict) -> list[dict]:
    """
    Convert raw indicator values into structured signals.
    Each signal: { indicator, signal, strength, value, interpretation }
    """
    signals = []

    # ── RSI ──────────────────────────────────────────────────
    rsi = indicators["rsi"]["value"]
    if rsi < 30:
        sig, strength = "buy", round((30 - rsi) / 30 * 100, 1)
        interp = f"RSI {rsi:.1f} — oversold territory, potential reversal upward"
    elif rsi > 70:
        sig, strength = "sell", round((rsi - 70) / 30 * 100, 1)
        interp = f"RSI {rsi:.1f} — overbought territory, potential pullback"
    else:
        sig, strength = "neutral", round(50 - abs(rsi - 50), 1)
        interp = f"RSI {rsi:.1f} — neutral momentum"
    signals.append({"indicator": "RSI", "signal": sig, "strength": strength,
                     "value": rsi, "interpretation": interp})

    # ── MACD ─────────────────────────────────────────────────
    macd_val = indicators["macd"]["value"]
    macd_sig = indicators["macd"]["signal_line"]
    diff = macd_val - macd_sig
    if diff > 0:
        sig, strength = "buy", min(round(abs(diff) * 10, 1), 100.0)
        interp = f"MACD crossed above signal line (diff: {diff:.3f})"
    elif diff < 0:
        sig, strength = "sell", min(round(abs(diff) * 10, 1), 100.0)
        interp = f"MACD crossed below signal line (diff: {diff:.3f})"
    else:
        sig, strength = "neutral", 0.0
        interp = "MACD at signal line"
    signals.append({"indicator": "MACD", "signal": sig, "strength": strength,
                     "value": macd_val, "interpretation": interp})

    # ── Bollinger Bands ───────────────────────────────────────
    price = indicators["bbands"]["price"]
    upper = indicators["bbands"]["upper"]
    lower = indicators["bbands"]["lower"]
    band_range = upper - lower
    if band_range > 0:
        position = (price - lower) / band_range   # 0 = at lower, 1 = at upper
    else:
        position = 0.5
    if position < 0.2:
        sig, strength = "buy", round((0.2 - position) / 0.2 * 100, 1)
        interp = f"Price near lower Bollinger Band ({price:.2f}), potential bounce"
    elif position > 0.8:
        sig, strength = "sell", round((position - 0.8) / 0.2 * 100, 1)
        interp = f"Price near upper Bollinger Band ({price:.2f}), potential reversal"
    else:
        sig, strength = "neutral", round(50 - abs(position - 0.5) * 100, 1)
        interp = f"Price within Bollinger Bands ({price:.2f})"
    signals.append({"indicator": "Bollinger Bands", "signal": sig, "strength": strength,
                     "value": price, "interpretation": interp})

    # ── MA Crossover ──────────────────────────────────────────
    ma50  = indicators["ma_cross"]["ma50"]
    ma200 = indicators["ma_cross"]["ma200"]
    if ma50 > ma200:
        gap_pct = (ma50 - ma200) / ma200 * 100
        sig, strength = "buy", min(round(gap_pct * 5, 1), 100.0)
        interp = f"Golden cross: MA50 ({ma50:.2f}) above MA200 ({ma200:.2f})"
    elif ma50 < ma200:
        gap_pct = (ma200 - ma50) / ma200 * 100
        sig, strength = "sell", min(round(gap_pct * 5, 1), 100.0)
        interp = f"Death cross: MA50 ({ma50:.2f}) below MA200 ({ma200:.2f})"
    else:
        sig, strength = "neutral", 0.0
        interp = "MA50 and MA200 are equal"
    signals.append({"indicator": "MA Crossover", "signal": sig, "strength": strength,
                     "value": ma50, "interpretation": interp})

    # ── Volume Profile ────────────────────────────────────────
    vol_5  = indicators["volume"]["vol_5"]
    vol_20 = indicators["volume"]["vol_20"]
    if vol_20 > 0:
        vol_ratio = vol_5 / vol_20
    else:
        vol_ratio = 1.0
    if vol_ratio > 1.2:
        sig, strength = "buy", min(round((vol_ratio - 1) * 100, 1), 100.0)
        interp = f"Volume surge: recent avg {vol_ratio:.2f}x the 20-day avg"
    elif vol_ratio < 0.8:
        sig, strength = "sell", min(round((1 - vol_ratio) * 100, 1), 100.0)
        interp = f"Volume declining: recent avg {vol_ratio:.2f}x the 20-day avg"
    else:
        sig, strength = "neutral", 50.0
        interp = f"Volume in line with average (ratio: {vol_ratio:.2f})"
    signals.append({"indicator": "Volume Profile", "signal": sig, "strength": strength,
                     "value": vol_5, "interpretation": interp})

    # ── ATR (context only, always neutral) ────────────────────
    atr = indicators["atr"]["value"]
    price = indicators["atr"]["price"]
    atr_pct = (atr / price * 100) if price > 0 else 0
    signals.append({"indicator": "ATR", "signal": "neutral", "strength": 50.0,
                     "value": atr,
                     "interpretation": f"ATR {atr:.2f} ({atr_pct:.1f}% of price) — volatility context"})

    return signals