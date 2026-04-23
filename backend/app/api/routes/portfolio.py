import asyncio
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone
import httpx
from app.schemas.portfolio import (
    BrokerAccountLink, BrokerAccount, Holding,
    PortfolioSummary, Transaction, BrokerName
)
from app.core.dependencies import get_current_user, rate_limit
from app.core.supabase import supabase
from app.core.security import encrypt_token, decrypt_token
from app.services.broker.broker_factory import BrokerFactory
from loguru import logger

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


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
        logger.warning(f"Rate limit bypassed for {endpoint} due to Redis degradation: {exc}")


from decimal import Decimal

def _cast_decimals(data: Any) -> Any:
    if isinstance(data, list):
        return [_cast_decimals(i) for i in data]
    if isinstance(data, dict):
        return {k: _cast_decimals(v) for k, v in data.items()}
    if isinstance(data, Decimal):
        return float(data)
    return data


async def _execute_query(query, *, operation: str, fail_open: bool = False):
    try:
        result = await asyncio.to_thread(query.execute)
        if result and result.data:
            result.data = _cast_decimals(result.data)
        return result
    except Exception as exc:
        if fail_open:
            logger.warning(f"{operation} skipped due to DB degradation: {exc}")
            return None
        if _is_connectivity_error(exc):
            logger.error(f"{operation} failed due to DB connectivity: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable. Check SUPABASE_URL/network and retry.",
            )
        logger.error(f"{operation} failed: {exc}")
        raise HTTPException(status_code=500, detail=f"{operation} failed")


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    await _apply_rate_limit(request, "portfolio_summary")
    # Aggregate holdings across all linked broker accounts
    holdings_result = await _execute_query(
        supabase.table("holdings")
        .select("*")
        .eq("user_id", current_user["id"]),
        operation="portfolio_holdings_summary_fetch",
    )
    holdings = holdings_result.data or []

    if not holdings:
        return PortfolioSummary(
            total_invested=0, total_current_value=0,
            total_unrealized_pnl=0, total_unrealized_pnl_pct=0,
            day_change=0, day_change_pct=0,
            holdings_count=0, brokers_connected=0, top_holdings=[],
        )

    total_invested = sum(h["invested_value"] for h in holdings)
    total_current = sum(h["current_value"] for h in holdings)
    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0
    day_change = sum(h.get("day_change", 0) for h in holdings)

    brokers_result = await _execute_query(
        supabase.table("broker_accounts")
        .select("id")
        .eq("user_id", current_user["id"])
        .eq("is_active", True),
        operation="portfolio_broker_count_fetch",
        fail_open=True,
    )

    top = sorted(holdings, key=lambda h: h["current_value"], reverse=True)[:5]

    return PortfolioSummary(
        total_invested=total_invested,
        total_current_value=total_current,
        total_unrealized_pnl=total_pnl,
        total_unrealized_pnl_pct=total_pnl_pct,
        day_change=day_change,
        day_change_pct=(day_change / total_current * 100) if total_current else 0,
        holdings_count=len(holdings),
        brokers_connected=len(brokers_result.data or []),
        top_holdings=top,
    )


@router.get("/holdings", response_model=list[Holding])
async def get_holdings(current_user: dict = Depends(get_current_user)):
    result = await _execute_query(
        supabase.table("holdings")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("current_value", desc=True),
        operation="portfolio_holdings_fetch",
    )
    return result.data or []


@router.get("/transactions", response_model=list[Transaction])
async def get_transactions(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
):
    result = await _execute_query(
        supabase.table("transactions")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("transaction_date", desc=True)
        .limit(limit),
        operation="portfolio_transactions_fetch",
    )
    return result.data or []


# ── Broker account management ─────────────────────────────────────────────────

@router.get("/brokers", response_model=list[BrokerAccount])
async def list_broker_accounts(current_user: dict = Depends(get_current_user)):
    result = await _execute_query(
        supabase.table("broker_accounts")
        .select("id, broker, account_id, display_name, is_active, last_synced_at, created_at")
        .eq("user_id", current_user["id"]),
        operation="portfolio_broker_accounts_fetch",
    )
    return result.data or []


@router.post("/brokers/sync/{broker_account_id}")
async def sync_broker(
    broker_account_id: str,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    """Trigger a manual sync of holdings from the broker."""
    await _apply_rate_limit(request, "broker_sync", limit=5, window=300)

    account = await _execute_query(
        supabase.table("broker_accounts")
        .select("*")
        .eq("id", broker_account_id)
        .eq("user_id", current_user["id"])
        .single(),
        operation=f"broker_account_fetch:{broker_account_id}",
    )
    if not account.data:
        raise HTTPException(status_code=404, detail="Broker account not found")

    acc = account.data
    try:
        access_token = decrypt_token(acc["access_token_encrypted"])
        broker = BrokerFactory.get_broker(acc["broker"])
        holdings = await broker.fetch_holdings(
            api_key=acc.get("api_key"),
            access_token=access_token,
        )

        # Upsert holdings into DB
        holdings_to_upsert = []
        for h in holdings:
            h["user_id"] = current_user["id"]
            h["broker_account_id"] = broker_account_id
            holdings_to_upsert.append(h)
        
        if holdings_to_upsert:
            await _execute_query(
                supabase.table("holdings").upsert(
                    holdings_to_upsert,
                    on_conflict="broker_account_id,ticker",
                ),
                operation=f"broker_holdings_upsert:{broker_account_id}",
            )

        # Update last_synced_at
        await _execute_query(
            supabase.table("broker_accounts").update(
                {"last_synced_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", broker_account_id),
            operation=f"broker_last_synced_update:{broker_account_id}",
            fail_open=True,
        )

        return {"message": "Sync successful", "holdings_synced": len(holdings)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Broker sync failed for {broker_account_id}: {e}")
        raise HTTPException(status_code=500, detail="Broker sync failed")


@router.delete("/brokers/{broker_account_id}")
async def unlink_broker(
    broker_account_id: str,
    current_user: dict = Depends(get_current_user),
):
    await _execute_query(
        supabase.table("broker_accounts").delete().eq(
        "id", broker_account_id
        ).eq("user_id", current_user["id"]),
        operation=f"broker_unlink:{broker_account_id}",
    )
    return {"message": "Broker account unlinked"}
