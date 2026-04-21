"""
Feature engineering: compute technical indicators from OHLCV DataFrame.
Uses pandas-ta for indicator calculations.
"""
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Optional

# Canonical feature set used by the LSTM.  Order is fixed — do not reorder.
LSTM_FEATURE_COLS: list[str] = [
    "rsi", "macd", "macd_hist", "macd_signal",
    "ema_20", "ema_50", "ema_200",
    "bb_upper", "bb_lower", "bb_width",
    "atr", "stoch_k", "stoch_d",
    "obv", "volume_ratio",
    "return_1d", "return_5d", "return_20d", "volatility_20d",
    "dist_from_52w_high", "dist_from_52w_low",
]


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: DataFrame with columns [Open, High, Low, Close, Volume]
    Output: DataFrame with 20+ technical indicator columns appended
    """
    df = df.copy()

    # Trend
    df["ema_20"] = ta.ema(df["Close"], length=20)
    df["ema_50"] = ta.ema(df["Close"], length=50)
    df["ema_200"] = ta.ema(df["Close"], length=200)

    # Momentum
    df["rsi"] = ta.rsi(df["Close"], length=14)
    macd = ta.macd(df["Close"])
    if macd is not None:
        df["macd"] = macd["MACD_12_26_9"]
        df["macd_signal"] = macd["MACDs_12_26_9"]
        df["macd_hist"] = macd["MACDh_12_26_9"]

    stoch = ta.stoch(df["High"], df["Low"], df["Close"])
    if stoch is not None:
        # pandas-ta 0.4.x: STOCHk_14_3_3, STOCHd_14_3_3
        stoch_k_col = [c for c in stoch.columns if "STOCHk" in c][0]
        stoch_d_col = [c for c in stoch.columns if "STOCHd" in c][0]
        df["stoch_k"] = stoch[stoch_k_col]
        df["stoch_d"] = stoch[stoch_d_col]

    # Volatility
    bb = ta.bbands(df["Close"], length=20)
    if bb is not None:
        # pandas-ta 0.4.x uses suffix format BBU_20_2.0_2.0
        bb_upper_col = [c for c in bb.columns if c.startswith("BBU")][0]
        bb_middle_col = [c for c in bb.columns if c.startswith("BBM")][0]
        bb_lower_col = [c for c in bb.columns if c.startswith("BBL")][0]
        df["bb_upper"] = bb[bb_upper_col]
        df["bb_middle"] = bb[bb_middle_col]
        df["bb_lower"] = bb[bb_lower_col]
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]

    df["atr"] = ta.atr(df["High"], df["Low"], df["Close"], length=14)

    # Volume
    df["obv"] = ta.obv(df["Close"], df["Volume"])
    df["volume_sma"] = df["Volume"].rolling(20).mean()
    df["volume_ratio"] = df["Volume"] / df["volume_sma"]

    # Price features
    df["return_1d"] = df["Close"].pct_change(1)
    df["return_5d"] = df["Close"].pct_change(5)
    df["return_20d"] = df["Close"].pct_change(20)
    df["volatility_20d"] = df["return_1d"].rolling(20).std() * np.sqrt(252)

    # Support / Resistance proximity
    df["dist_from_52w_high"] = (df["Close"] - df["Close"].rolling(252).max()) / df["Close"]
    df["dist_from_52w_low"] = (df["Close"] - df["Close"].rolling(252).min()) / df["Close"]

    return df.dropna()


def get_latest_features(df: pd.DataFrame) -> dict:
    """Return the most recent row's features as a dict."""
    featured = compute_features(df)
    if featured.empty:
        return {}
    last = featured.iloc[-1]
    return {
        "rsi": last.get("rsi"),
        "macd": last.get("macd"),
        "macd_signal": last.get("macd_signal"),
        "macd_hist": last.get("macd_hist"),
        "ema_20": last.get("ema_20"),
        "ema_50": last.get("ema_50"),
        "ema_200": last.get("ema_200"),
        "bb_upper": last.get("bb_upper"),
        "bb_middle": last.get("bb_middle"),
        "bb_lower": last.get("bb_lower"),
        "atr": last.get("atr"),
        "obv": last.get("obv"),
        "stoch_k": last.get("stoch_k"),
        "stoch_d": last.get("stoch_d"),
        "return_1d": last.get("return_1d"),
        "return_5d": last.get("return_5d"),
        "volatility_20d": last.get("volatility_20d"),
    }
