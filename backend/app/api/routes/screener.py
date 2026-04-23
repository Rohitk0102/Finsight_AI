import asyncio
import httpx
import uuid
from fastapi import APIRouter, Query, Depends, Request, HTTPException
from app.core.dependencies import get_current_user, rate_limit
from app.core.redis import redis_get, redis_set
from app.core.supabase import supabase
from app.services.data.stock_fetcher import StockDataFetcher
from app.services.data.screener_service import ScreenerService
from typing import Optional
import hashlib
import json
from loguru import logger

router = APIRouter(prefix="/screener", tags=["screener"])
fetcher = StockDataFetcher()
screener_service = ScreenerService()


def _request_ip(request: Request | None) -> str:
    if request and request.client and request.client.host:
        return request.client.host
    return "unknown"


def _is_connectivity_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPError):
        return True
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "nodename nor servname provided",
            "name or service not known",
            "temporary failure in name resolution",
            "connection refused",
            "timed out",
        )
    )


async def _apply_rate_limit(
    request: Request | None,
    endpoint: str,
    *,
    limit: int = 60,
    window: int = 60,
) -> None:
    try:
        await rate_limit(_request_ip(request), endpoint, limit=limit, window=window)
    except HTTPException:
        raise
    except Exception as exc:
        # Redis degradation should not fail screen requests.
        logger.warning(f"Rate limit bypassed for {endpoint}: {exc}")


async def _execute_query(query, *, operation: str):
    try:
        res = await asyncio.to_thread(query.execute)
        return res
    except Exception as exc:
        logger.error(f"Screener query failed ({operation}): {exc}")
        if _is_connectivity_error(exc):
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable. Check SUPABASE_URL/network and retry.",
            )
        raise HTTPException(status_code=500, detail=f"{operation} failed: {str(exc)}")


@router.get("/scan")
async def scan_stocks(
    signal: Optional[str] = Query(None, description="BUY | SELL | HOLD"),
    sector: Optional[str] = None,
    min_market_cap: Optional[float] = None,
    max_pe: Optional[float] = None,
    min_rsi: Optional[float] = None,
    max_rsi: Optional[float] = None,
    exchange: Optional[str] = Query("NSE", description="NSE | BSE | NASDAQ"),
    limit: int = Query(20, le=50),
    request: Request = None,
):
    """Screen stocks by technical + fundamental filters."""
    await _apply_rate_limit(request, "screener", limit=20, window=60)

    filters = {"signal": signal, "sector": sector, "min_market_cap": min_market_cap,
               "max_pe": max_pe, "min_rsi": min_rsi, "max_rsi": max_rsi,
               "exchange": exchange, "limit": limit}
    cache_key = "screener:" + hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()
    cached = await redis_get(cache_key)
    if cached:
        return cached

    results = await screener_service.scan_stocks(filters)
    await redis_set(cache_key, results, ttl=600)
    return results


@router.get("/watchlist")
async def get_watchlist(current_user: dict = Depends(get_current_user)):
    result = await _execute_query(
        supabase.table("watchlists")
        .select("*")
        .eq("user_id", current_user["id"]),
        operation="watchlist_fetch",
    )
    return result.data or []


@router.post("/watchlist/{ticker}")
async def add_to_watchlist(ticker: str, current_user: dict = Depends(get_current_user)):
    # 1. Ensure user profile exists (foreign key constraint)
    # We do a quick check/upsert for the user profile
    try:
        profile_check = await asyncio.to_thread(
            lambda: supabase.table("user_profiles").select("clerk_id").eq("clerk_id", current_user["id"]).execute()
        )
        if not profile_check.data:
            logger.info(f"Auto-creating user profile for {current_user['id']} during watchlist add")
            await asyncio.to_thread(
                lambda: supabase.table("user_profiles").insert({
                    "clerk_id": current_user["id"],
                    "email": current_user.get("email", ""),
                }).execute()
            )
    except Exception as e:
        logger.warning(f"Failed to ensure user profile exists: {e}")
        # We continue anyway, the next query will fail if it's a hard FK issue

    # 2. Add to watchlist
    await _execute_query(
        supabase.table("watchlists").upsert(
            {
                "user_id": current_user["id"],
                "ticker": ticker.upper(),
            },
            on_conflict="user_id,ticker",
        ),
        operation="watchlist_upsert",
    )
    return {"message": f"{ticker.upper()} added to watchlist"}


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str, current_user: dict = Depends(get_current_user)):
    await _execute_query(
        supabase.table("watchlists").delete().eq(
            "user_id", current_user["id"]
        ).eq("ticker", ticker.upper()),
        operation="watchlist_delete",
    )
    return {"message": f"{ticker.upper()} removed from watchlist"}

@router.get("/metadata")
async def get_screener_metadata():
    """Get unique sectors and exchanges for filters."""
    return await screener_service.get_metadata()
