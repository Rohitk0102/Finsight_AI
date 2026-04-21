"""
Market regime detection: bull / bear / sideways.

Algorithm:
  - 20-day rolling return  → trend direction
  - 20-day annualised vol  → volatility regime
  - 200-day EMA slope      → long-term trend confirmation

Classification:
  bull      : rolling_ret > +1.5%  AND  below normal vol
  bear      : rolling_ret < -1.5%  OR   high vol + negative trend
  sideways  : otherwise
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Literal

MarketRegime = Literal["bull", "bear", "sideways"]


def detect_regime(df: pd.DataFrame) -> MarketRegime:
    """
    Detect market regime from an OHLCV DataFrame (at least 200 rows recommended).

    Parameters
    ----------
    df : pd.DataFrame
        Must have a 'Close' column.

    Returns
    -------
    "bull" | "bear" | "sideways"
    """
    if df.empty or len(df) < 20:
        return "sideways"

    close = df["Close"].astype(float)

    # 20-day rolling return (momentum)
    ret_20 = float(close.pct_change(20).iloc[-1]) if len(close) >= 20 else 0.0

    # Annualised 20-day volatility
    daily_rets = close.pct_change().dropna()
    vol_20 = float(daily_rets.tail(20).std() * np.sqrt(252)) if len(daily_rets) >= 20 else 0.3

    # 200-day EMA slope (positive = long-term up-trend)
    if len(close) >= 200:
        ema200 = close.ewm(span=200, adjust=False).mean()
        ema_slope = float((ema200.iloc[-1] - ema200.iloc[-5]) / (ema200.iloc[-5] + 1e-9))
    else:
        ema_slope = 0.0

    # Thresholds
    HIGH_VOL = 0.35   # annualised vol > 35% → high volatility
    BULL_RET = 0.015  # 20-day return > 1.5%
    BEAR_RET = -0.015 # 20-day return < -1.5%

    if ret_20 > BULL_RET and vol_20 < HIGH_VOL and ema_slope >= 0:
        return "bull"
    elif ret_20 < BEAR_RET or (vol_20 >= HIGH_VOL and ret_20 < 0):
        return "bear"
    return "sideways"
