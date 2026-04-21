from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

import httpx
from loguru import logger

from app.core.supabase import supabase
from app.schemas.markets import BookmarkCreate, BookmarkRecord, PortfolioPosition, PriceAlertCreate, PriceAlertResponse


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


class MarketRepositoryError(RuntimeError):
    pass


class MarketRepositoryUnavailableError(MarketRepositoryError):
    pass


class MarketRepository:
    def __init__(self, client=supabase) -> None:
        self.client = client

    async def _execute_query(self, query, *, operation: str, fail_open: bool = False):
        try:
            return await asyncio.to_thread(query.execute)
        except Exception as exc:
            if fail_open:
                logger.warning(f"{operation} skipped due to DB degradation: {exc}")
                return None
            if _is_connectivity_error(exc):
                raise MarketRepositoryUnavailableError(operation) from exc
            logger.error(f"{operation} failed: {exc}")
            raise MarketRepositoryError(operation) from exc

    async def load_watchlist_symbols(self, user_id: Optional[str]) -> list[str]:
        if not user_id:
            return []
        result = await self._execute_query(
            self.client.table("market_watchlists").select("symbol").eq("user_id", user_id).order("created_at", desc=True),
            operation="market_watchlist_fetch",
            fail_open=True,
        )
        data = result.data if result else []
        return [row["symbol"] for row in (data or [])]

    async def load_recent_symbols(self, user_id: Optional[str], *, limit: int = 5) -> list[str]:
        if not user_id:
            return []
        result = await self._execute_query(
            self.client.table("market_recent_views")
            .select("symbol")
            .eq("user_id", user_id)
            .order("last_viewed_at", desc=True)
            .limit(limit),
            operation="market_recent_views_fetch",
            fail_open=True,
        )
        data = result.data if result else []
        return [row["symbol"] for row in (data or [])]

    async def load_bookmarked_urls(self, user_id: Optional[str]) -> set[str]:
        if not user_id:
            return set()
        result = await self._execute_query(
            self.client.table("market_article_bookmarks").select("source_url").eq("user_id", user_id),
            operation="market_bookmark_fetch",
            fail_open=True,
        )
        data = result.data if result else []
        return {row["source_url"] for row in (data or [])}

    async def list_bookmarks(self, user_id: str) -> list[BookmarkRecord]:
        result = await self._execute_query(
            self.client.table("market_article_bookmarks")
            .select("*")
            .eq("user_id", user_id)
            .order("published_at", desc=True),
            operation="market_bookmarks_list",
            fail_open=True,
        )
        data = result.data if result else []
        return [BookmarkRecord.model_validate(row) for row in (data or [])]

    async def add_bookmark(self, user_id: str, payload: BookmarkCreate) -> None:
        await self._execute_query(
            self.client.table("market_article_bookmarks").upsert(
                {
                    "user_id": user_id,
                    "article_id": payload.articleId,
                    "title": payload.title,
                    "source_url": payload.sourceUrl,
                    "source": payload.source,
                    "published_at": payload.publishedAt.isoformat(),
                },
                on_conflict="user_id,source_url",
            ),
            operation="market_bookmark_upsert",
        )

    async def delete_bookmark(self, user_id: str, article_id: str) -> None:
        await self._execute_query(
            self.client.table("market_article_bookmarks")
            .delete()
            .eq("user_id", user_id)
            .eq("article_id", article_id),
            operation="market_bookmark_delete",
        )

    async def upsert_watchlist(self, user_id: str, *, symbol: str, exchange: str, notes: Optional[str]) -> None:
        await self._execute_query(
            self.client.table("market_watchlists").upsert(
                {
                    "user_id": user_id,
                    "symbol": symbol,
                    "exchange": exchange,
                    "notes": notes,
                },
                on_conflict="user_id,symbol",
            ),
            operation="market_watchlist_upsert",
        )

    async def delete_watchlist(self, user_id: str, symbol: str) -> None:
        await self._execute_query(
            self.client.table("market_watchlists")
            .delete()
            .eq("user_id", user_id)
            .eq("symbol", symbol),
            operation="market_watchlist_delete",
        )

    async def list_alerts(self, user_id: str) -> list[PriceAlertResponse]:
        result = await self._execute_query(
            self.client.table("market_price_alerts")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True),
            operation="market_alerts_list",
            fail_open=True,
        )
        data = result.data if result else []
        return [
            PriceAlertResponse(
                id=row["id"],
                symbol=row["symbol"],
                exchange=row["exchange"],
                alertType=row["alert_type"],
                thresholdValue=float(row["threshold_value"]),
                isActive=bool(row.get("is_active", True)),
                createdAt=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                if isinstance(row["created_at"], str)
                else row["created_at"],
            )
            for row in (data or [])
        ]

    async def create_alert(self, user_id: str, payload: PriceAlertCreate, *, symbol: str) -> None:
        await self._execute_query(
            self.client.table("market_price_alerts").insert(
                {
                    "user_id": user_id,
                    "symbol": symbol,
                    "exchange": payload.exchange,
                    "alert_type": payload.alertType,
                    "threshold_value": payload.thresholdValue,
                    "is_active": True,
                }
            ),
            operation="market_alert_create",
        )

    async def delete_alert(self, user_id: str, alert_id: str) -> None:
        await self._execute_query(
            self.client.table("market_price_alerts")
            .delete()
            .eq("user_id", user_id)
            .eq("id", alert_id),
            operation="market_alert_delete",
        )

    async def upsert_recent_view(self, user_id: Optional[str], symbol: str) -> None:
        if not user_id:
            return
        await self._execute_query(
            self.client.table("market_recent_views").upsert(
                {
                    "user_id": user_id,
                    "symbol": symbol,
                    "last_viewed_at": datetime.now(timezone.utc).isoformat(),
                },
                on_conflict="user_id,symbol",
            ),
            operation="market_recent_view_upsert",
            fail_open=True,
        )

    async def get_portfolio_position(self, user_id: Optional[str], symbol: str):
        if not user_id:
            return None
        result = await self._execute_query(
            self.client.table("holdings")
            .select("*")
            .eq("user_id", user_id)
            .in_("ticker", [symbol, f"{symbol}.NS", f"{symbol}.BO"]),
            operation="market_portfolio_context_fetch",
            fail_open=True,
        )
        rows = result.data if result else []
        if not rows:
            return None
        row = rows[0]
        return PortfolioPosition(
            quantity=float(row["quantity"]),
            averagePrice=float(row["average_price"]),
            currentValue=float(row["current_value"]),
            investedValue=float(row["invested_value"]),
            unrealizedPnl=float(row["unrealized_pnl"]),
            unrealizedPnlPct=float(row["unrealized_pnl_pct"]),
            dayChangePct=float(row.get("day_change_pct", 0)),
        )
