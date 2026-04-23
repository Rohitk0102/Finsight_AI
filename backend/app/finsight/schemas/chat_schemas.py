from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class MarketData(BaseModel):
    symbol: str
    price: float
    change_pct: float
    volume: Optional[int] = None
    source: str = "yfinance"

class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: str
    stream: bool = False

class ChatResponse(BaseModel):
    reply: str
    intent: str
    tickers_mentioned: List[str] = Field(default_factory=list)
    sentiment_score: Optional[float] = None
    market_data: List[MarketData] = Field(default_factory=list)
    timestamp: str

class PortfolioItem(BaseModel):
    symbol: str
    quantity: float
    avg_price: float

class PortfolioAnalysis(BaseModel):
    total_value: float
    day_change_pct: float
    beta: float
    sharpe_ratio: float
    risk_level: str
    top_performer: Optional[str] = None
    bottom_performer: Optional[str] = None
    allocation: Dict[str, float] = Field(default_factory=dict)
