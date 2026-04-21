"""
Portfolio diversification and concentration scoring.

Metrics:
  diversification_score : 1 − avg(|pairwise_correlation|) across all ticker pairs.
                           1.0 = perfectly uncorrelated, 0.0 = perfectly correlated.
  concentration_risk    : Herfindahl–Hirschman Index (HHI) on equal-weighted positions.
                           Values near 1/N = well-spread, near 1.0 = fully concentrated.
  most_correlated_pair  : (ticker_a, ticker_b, correlation) — highest absolute corr pair.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger
from typing import Optional


def score_portfolio(tickers: list[str], window: int = 60) -> dict:
    """
    Compute diversification metrics for a list of tickers.

    Parameters
    ----------
    tickers : list of ticker strings (min 2).
    window  : lookback in trading days for return correlation.

    Returns
    -------
    {
      "diversification_score": float,   # 0–1
      "concentration_risk": float,       # 0–1
      "risk_level": str,                 # "low" | "moderate" | "high"
      "most_correlated_pair": list | None,
      "n_tickers": int,
    }
    """
    tickers = list(dict.fromkeys(tickers))  # deduplicate, preserve order

    if len(tickers) < 2:
        return {
            "diversification_score": 1.0,
            "concentration_risk": 1.0,
            "risk_level": "high",
            "most_correlated_pair": None,
            "n_tickers": len(tickers),
        }

    try:
        raw = yf.download(
            tickers,
            period=f"{window + 10}d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )
        if raw.empty:
            raise ValueError("yfinance returned empty data")

        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"].dropna(how="all")
        else:
            close = raw.dropna(how="all")

        # Keep only tickers that have data
        close = close.dropna(axis=1, thresh=window // 2)
        valid = [t for t in tickers if t in close.columns]

        if len(valid) < 2:
            raise ValueError("Fewer than 2 tickers have sufficient data")

        rets = close[valid].pct_change().dropna()
        corr_matrix = rets.corr()

        # Pairwise correlations (upper triangle, excluding diagonal)
        n = len(valid)
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                c = corr_matrix.iloc[i, j]
                pairs.append((valid[i], valid[j], float(c)))

        abs_corrs = [abs(p[2]) for p in pairs]
        avg_abs_corr = float(np.mean(abs_corrs)) if abs_corrs else 0.0
        diversification_score = round(1.0 - avg_abs_corr, 4)

        # Concentration risk (equal-weighted HHI)
        weight = 1.0 / n
        hhi = float(n * weight ** 2)  # equal-weight HHI = 1/n
        concentration_risk = round(hhi, 4)

        # Most correlated pair
        if pairs:
            worst = max(pairs, key=lambda p: abs(p[2]))
            most_correlated_pair = [worst[0], worst[1], round(worst[2], 4)]
        else:
            most_correlated_pair = None

        # Risk classification
        if diversification_score >= 0.6:
            risk_level = "low"
        elif diversification_score >= 0.35:
            risk_level = "moderate"
        else:
            risk_level = "high"

        return {
            "diversification_score": diversification_score,
            "concentration_risk": concentration_risk,
            "risk_level": risk_level,
            "most_correlated_pair": most_correlated_pair,
            "n_tickers": n,
        }

    except Exception as exc:
        logger.warning(f"Portfolio scoring failed: {exc}")
        return {
            "diversification_score": None,
            "concentration_risk": None,
            "risk_level": "unknown",
            "most_correlated_pair": None,
            "n_tickers": len(tickers),
        }
