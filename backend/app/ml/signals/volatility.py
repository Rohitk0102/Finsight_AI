"""
Volatility forecasting via GARCH(1,1).

Returns annualised volatility forecast for the next N days.
Falls back to realised 20-day vol if arch is not installed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger
from typing import Optional


def forecast_volatility(df: pd.DataFrame, horizon: int = 7) -> Optional[float]:
    """
    Fit a GARCH(1,1) model on daily percentage returns and return
    the annualised volatility forecast over *horizon* trading days.

    Parameters
    ----------
    df      : OHLCV DataFrame with a 'Close' column.
    horizon : number of trading days to forecast.

    Returns
    -------
    Annualised volatility as a float (e.g. 0.25 = 25%), or None on failure.
    """
    close = df["Close"].dropna().astype(float)
    if len(close) < 60:
        return None

    # Percentage returns (arch expects %, not decimal)
    pct_returns = close.pct_change().dropna() * 100

    try:
        from arch import arch_model

        am = arch_model(pct_returns, vol="Garch", p=1, q=1, dist="normal")
        res = am.fit(disp="off", show_warning=False)
        fc = res.forecast(horizon=horizon)
        # variance is in (%^2), take sqrt for daily std in %
        daily_vol_pct = float(np.sqrt(fc.variance.values[-1, -1]))
        # Annualise and convert to decimal
        annualised = (daily_vol_pct / 100) * np.sqrt(252)
        return round(float(annualised), 4)

    except ImportError:
        # Fallback: realised 20-day annualised vol
        realised = float(pct_returns.tail(20).std() / 100 * np.sqrt(252))
        return round(realised, 4)

    except Exception as exc:
        logger.warning(f"GARCH fit failed: {exc}")
        realised = float(pct_returns.tail(20).std() / 100 * np.sqrt(252))
        return round(realised, 4)
