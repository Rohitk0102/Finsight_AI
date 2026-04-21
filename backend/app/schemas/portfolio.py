from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class BrokerName(str, Enum):
    ZERODHA = "zerodha"
    UPSTOX = "upstox"
    ANGEL_ONE = "angel_one"
    GROWW = "groww"


class BrokerAccountLink(BaseModel):
    broker: BrokerName
    api_key: Optional[str] = None         # For Zerodha / Angel One
    access_token: Optional[str] = None    # After OAuth


class BrokerAccount(BaseModel):
    id: str
    user_id: str
    broker: BrokerName
    account_id: Optional[str]             # broker-assigned account ID
    display_name: Optional[str]
    is_active: bool
    last_synced_at: Optional[datetime]
    created_at: datetime


class Holding(BaseModel):
    id: str
    broker_account_id: str
    ticker: str
    name: str
    quantity: float
    average_price: float
    current_price: float
    current_value: float
    invested_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    day_change: float
    day_change_pct: float
    last_updated: datetime


class PortfolioSummary(BaseModel):
    total_invested: float
    total_current_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    day_change: float
    day_change_pct: float
    holdings_count: int
    brokers_connected: int
    top_holdings: list[Holding]


class Transaction(BaseModel):
    id: str
    broker_account_id: str
    ticker: str
    transaction_type: str   # BUY | SELL
    quantity: float
    price: float
    total_value: float
    transaction_date: datetime
    charges: Optional[float] = 0.0
