from fastapi import APIRouter, Query, HTTPException, Depends, Request
from app.schemas.stock import StockDetail, OHLCVData, StockSearchResult
from app.core.dependencies import get_current_user, rate_limit
from app.core.redis import redis_get, redis_set
from app.services.data.stock_fetcher import StockDataFetcher
from typing import Optional
from loguru import logger

router = APIRouter(prefix="/stocks", tags=["stocks"])
fetcher = StockDataFetcher()


@router.get("/search", response_model=list[StockSearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1, max_length=20),
    exchange: Optional[str] = Query(None, description="NSE | BSE | NASDAQ | NYSE"),
    request: Request = None,
):
    await rate_limit(request.client.host, "stock_search")
    cache_key = f"search:{q.upper()}:{exchange}"
    cached = await redis_get(cache_key)
    if cached:
        return cached

    results = await fetcher.search_stocks(q, exchange)
    await redis_set(cache_key, [r.model_dump() for r in results], ttl=3600)
    return results


@router.get("/{ticker}", response_model=StockDetail)
async def get_stock_detail(ticker: str, request: Request):
    await rate_limit(request.client.host, "stock_detail")
    ticker = ticker.upper()
    cache_key = f"stock_detail:{ticker}"
    cached = await redis_get(cache_key)
    if cached:
        return cached

    data = await fetcher.get_stock_detail(ticker)
    if not data:
        raise HTTPException(status_code=404, detail=f"Stock '{ticker}' not found")

    await redis_set(cache_key, data.model_dump(), ttl=60)
    return data


@router.get("/{ticker}/ohlcv", response_model=list[OHLCVData])
async def get_ohlcv(
    ticker: str,
    period: str = Query("1y", description="1d | 5d | 1mo | 3mo | 6mo | 1y | 2y | 5y"),
    interval: str = Query("1d", description="1d | 1wk | 1mo"),
    request: Request = None,
):
    await rate_limit(request.client.host, "ohlcv")
    ticker = ticker.upper()
    cache_key = f"ohlcv:{ticker}:{period}:{interval}"
    cached = await redis_get(cache_key)
    if cached:
        return cached

    data = await fetcher.get_ohlcv(ticker, period, interval)
    ttl = 60 if interval == "1d" else 3600
    await redis_set(cache_key, [d.model_dump() for d in data], ttl=ttl)
    return data


@router.get("/{ticker}/price")
async def get_live_price(ticker: str, request: Request):
    """Real-time price — 60-second cache."""
    await rate_limit(request.client.host, "live_price")
    ticker = ticker.upper()
    cache_key = f"price:{ticker}"
    cached = await redis_get(cache_key)
    if cached:
        return cached

    price_data = await fetcher.get_live_price(ticker)
    await redis_set(cache_key, price_data, ttl=60)
    return price_data
