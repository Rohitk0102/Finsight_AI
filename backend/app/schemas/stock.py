from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date, datetime
from enum import Enum


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RiskLabel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


# Possible market regime values
MarketRegime = Literal["bull", "bear", "sideways"]


class StockSearchResult(BaseModel):
    ticker: str
    name: str
    exchange: str
    sector: Optional[str]
    industry: Optional[str]


class OHLCVData(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float]


class TechnicalIndicators(BaseModel):
    rsi: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_hist: Optional[float]
    ema_20: Optional[float]
    ema_50: Optional[float]
    ema_200: Optional[float]
    bb_upper: Optional[float]
    bb_middle: Optional[float]
    bb_lower: Optional[float]
    atr: Optional[float]
    obv: Optional[float]
    stoch_k: Optional[float]
    stoch_d: Optional[float]


class StockPrediction(BaseModel):
    ticker: str
    name: str
    current_price: float
    predicted_1d: float
    predicted_7d: float
    predicted_30d: float
    confidence: float           # 0.0 – 1.0
    signal: Signal
    risk_score: float           # 0.0 – 10.0
    risk_label: RiskLabel
    sentiment_score: float      # -1.0 – 1.0  (pre-computed FinBERT)
    regime: MarketRegime        # bull | bear | sideways
    model_version: str          # e.g. "xgb:v2|lstm:v1|prophet:v1"
    factors: list[str]          # human-readable reasoning
    technicals: TechnicalIndicators
    sector_correlation: Optional[float] = None   # rolling 60-day corr to sector ETF
    volatility_forecast: Optional[float] = None  # GARCH annualised vol
    generated_at: datetime


class PredictionAccuracy(BaseModel):
    ticker: str
    horizon_days: int
    model_version: str
    hit_rate: Optional[float]   # % direction-correct
    avg_mape: Optional[float]   # mean absolute % error
    n_samples: int
    computed_at: datetime


class StockDetail(BaseModel):
    ticker: str
    name: str
    exchange: str
    sector: Optional[str]
    industry: Optional[str]
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    eps: Optional[float]
    dividend_yield: Optional[float]
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    current_price: float
    price_change: float
    price_change_pct: float
    volume: int
    avg_volume: Optional[int]
