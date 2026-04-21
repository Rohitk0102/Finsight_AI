"""
Sector correlation: rolling 60-day Pearson correlation between a stock and
its sector benchmark.

Benchmarks:
  US stocks  → SPDR sector ETFs (XLK, XLF, ...)
  Indian .NS → Nifty sector indices (^CNXAUTO, ^CNXBANK, ...)
  Fallback   → Nifty 50 (^NSEI) or S&P 500 (^GSPC)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger
from typing import Optional

# ── Sector → benchmark mapping ────────────────────────────────────────────────

_US_SECTOR_ETF: dict[str, str] = {
    "Technology": "XLK",
    "Information Technology": "XLK",
    "Financials": "XLF",
    "Financial Services": "XLF",
    "Health Care": "XLV",
    "Healthcare": "XLV",
    "Energy": "XLE",
    "Consumer Discretionary": "XLY",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Utilities": "XLU",
    "Communication Services": "XLC",
    "Real Estate": "XLRE",
    "Consumer Staples": "XLP",
}

_INDIA_SECTOR_INDEX: dict[str, str] = {
    "Automobile": "^CNXAUTO",
    "Auto": "^CNXAUTO",
    "Banking": "^NSEBANK",
    "Financial Services": "^CNXFIN",
    "IT": "^CNXIT",
    "Technology": "^CNXIT",
    "Pharma": "^CNXPHARMA",
    "Healthcare": "^CNXPHARMA",
    "FMCG": "^CNXFMCG",
    "Consumer Staples": "^CNXFMCG",
    "Metals": "^CNXMETAL",
    "Materials": "^CNXMETAL",
    "Energy": "^CNXENERGY",
    "Realty": "^CNXREALTY",
    "Real Estate": "^CNXREALTY",
    "Media": "^CNXMEDIA",
}

_FALLBACK_US = "^GSPC"
_FALLBACK_IN = "^NSEI"


def _benchmark_for(ticker: str, sector: Optional[str]) -> str:
    is_indian = ticker.endswith(".NS") or ticker.endswith(".BO")
    if is_indian:
        if sector:
            for key, idx in _INDIA_SECTOR_INDEX.items():
                if key.lower() in sector.lower():
                    return idx
        return _FALLBACK_IN
    else:
        if sector:
            etf = _US_SECTOR_ETF.get(sector)
            if etf:
                return etf
        return _FALLBACK_US


def compute_sector_correlation(
    ticker: str,
    sector: Optional[str] = None,
    window: int = 60,
) -> Optional[float]:
    """
    Return the rolling *window*-day Pearson correlation between *ticker* and
    its sector benchmark. Returns None on failure.
    """
    benchmark = _benchmark_for(ticker, sector)
    try:
        raw = yf.download(
            [ticker, benchmark],
            period=f"{window + 10}d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )
        if raw.empty:
            return None

        # yfinance multi-ticker returns MultiIndex columns
        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"][[ticker, benchmark]].dropna()
        else:
            return None

        if len(close) < window // 2:
            return None

        rets = close.pct_change().dropna()
        corr = float(rets[ticker].corr(rets[benchmark]))
        return round(corr, 4) if not np.isnan(corr) else None

    except Exception as exc:
        logger.warning(
            f"Sector correlation failed for {ticker}/{benchmark}: {exc}",
            extra={"ticker": ticker},
        )
        return None
