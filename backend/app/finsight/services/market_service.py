import json
import yfinance as yf
import asyncio
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime
import pytz

from app.core.redis import get_redis
from app.finsight.schemas.chat_schemas import MarketData

class MarketService:
    @staticmethod
    async def get_ticker_data(symbol: str) -> Dict[str, Any]:
        redis = await get_redis()
        cache_key = f"ticker:{symbol}"
        cached = await redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
            
        try:
            # Run yfinance in a thread to avoid blocking
            data = await asyncio.to_thread(MarketService._fetch_yfinance_data, symbol)
            if data:
                await redis.setex(cache_key, 300, json.dumps(data))
                return data
            return {}
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return {}

    @staticmethod
    def _fetch_yfinance_data(symbol: str) -> Dict[str, Any]:
        t = yf.Ticker(symbol)
        info = t.info
        fast_info = t.fast_info
        
        # currentPrice fallback to regularMarketPrice
        price = info.get("currentPrice") or info.get("regularMarketPrice") or fast_info.get("lastPrice")
        if price is None:
            return {}
            
        return {
            "symbol": symbol,
            "price": price,
            "change_pct": info.get("regularMarketChangePercent") or 0.0,
            "volume": info.get("volume") or fast_info.get("lastVolume"),
            "pe_ratio": info.get("trailingPE"),
            "market_cap": info.get("marketCap") or fast_info.get("marketCap"),
            "52w_high": info.get("fiftyTwoWeekHigh") or fast_info.get("yearHigh"),
            "52w_low": info.get("fiftyTwoWeekLow") or fast_info.get("yearLow"),
            "source": "yfinance"
        }

    @staticmethod
    def is_market_open() -> bool:
        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        if now.weekday() >= 5: # Saturday or Sunday
            return False
        # NYSE hours: 9:30 AM to 4:00 PM
        if now.hour < 9 or (now.hour == 9 and now.minute < 30):
            return False
        if now.hour >= 16:
            return False
        return True

market_service = MarketService()
