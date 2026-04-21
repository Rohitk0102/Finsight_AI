from __future__ import annotations

import asyncio
from typing import Optional
import websockets.exceptions

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from loguru import logger

from app.core.config import settings
from app.core.dependencies import get_current_user, get_current_user_optional, rate_limit
from app.core.redis import redis_get, redis_set
from app.schemas.markets import (
    BookmarkCreate,
    BookmarkRecord,
    ChartRange,
    CompanyChartResponse,
    CompanyDetailResponse,
    EnrichedNewsArticle,
    MarketNewsFeedResponse,
    MarketOverviewResponse,
    MarketSocketMessage,
    MarketWatchlistEntry,
    MutationResponse,
    PriceAlertCreate,
    PriceAlertResponse,
    SearchContextResponse,
    SearchResult,
)
from app.services.markets import (
    MarketPulseService,
    MarketRepository,
    MarketRepositoryError,
    MarketRepositoryUnavailableError,
)

router = APIRouter(prefix="/markets", tags=["markets"])
market_service = MarketPulseService()
market_repository = MarketRepository()


def _feature_enabled() -> None:
    if not settings.FEATURE_MARKETS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Markets module is disabled")


def _request_ip(request: Request | None) -> str:
    if request and request.client and request.client.host:
        return request.client.host
    return "unknown"


async def _apply_rate_limit(request: Request | None, endpoint: str, *, limit: int = 60, window: int = 60) -> None:
    try:
        await rate_limit(_request_ip(request), endpoint, limit=limit, window=window)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Rate limit bypassed for markets {endpoint}: {exc}")


async def _repository_call(awaitable):
    try:
        return await awaitable
    except MarketRepositoryUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. Check SUPABASE_URL/network and retry.",
        )
    except MarketRepositoryError as exc:
        operation = exc.args[0] if exc.args else "market_repository"
        raise HTTPException(status_code=500, detail=f"{operation} failed")


def _with_bookmarks(
    articles: list[EnrichedNewsArticle],
    bookmarked_urls: set[str],
) -> list[EnrichedNewsArticle]:
    return [
        article.model_copy(update={"bookmarked": True}) if article.sourceUrl in bookmarked_urls else article
        for article in articles
    ]


@router.get("/overview", response_model=MarketOverviewResponse)
async def get_overview(
    request: Request = None,
    current_user: dict | None = Depends(get_current_user_optional),
):
    _feature_enabled()
    await _apply_rate_limit(request, "markets_overview")
    user_id = current_user["id"] if current_user else None
    watchlist_symbols, bookmarks = await asyncio.gather(
        _repository_call(market_repository.load_watchlist_symbols(user_id)),
        _repository_call(market_repository.load_bookmarked_urls(user_id)),
    )
    cache_key = f"markets:overview:{':'.join(sorted(watchlist_symbols[:6])) or 'anon'}"
    cached = await redis_get(cache_key)
    if cached and not user_id:
        return cached
    overview = await market_service.get_overview(watchlist_symbols, bookmarks)
    await redis_set(cache_key, overview.model_dump(mode="json"), ttl=120)
    return overview


@router.get("/search", response_model=list[SearchResult])
async def search_markets(
    q: str = Query(..., min_length=1, max_length=50),
    request: Request = None,
):
    _feature_enabled()
    await _apply_rate_limit(request, "markets_search")
    cache_key = f"markets:search:{q.upper()}"
    cached = await redis_get(cache_key)
    if cached:
        return cached
    results = await market_service.search(q)
    await redis_set(cache_key, [item.model_dump(mode="json") for item in results], ttl=120)
    return results


@router.get("/search/context", response_model=SearchContextResponse)
async def search_context(
    request: Request = None,
    current_user: dict | None = Depends(get_current_user_optional),
):
    _feature_enabled()
    await _apply_rate_limit(request, "markets_search_context")
    user_id = current_user["id"] if current_user else None
    if not user_id:
        cache_key = "markets:search_context:anon"
        cached = await redis_get(cache_key)
        if cached:
            return cached
        context = await market_service.get_search_context([])
        await redis_set(cache_key, context.model_dump(mode="json"), ttl=180)
        return context

    recent_symbols = await _repository_call(market_repository.load_recent_symbols(user_id))
    return await market_service.get_search_context(recent_symbols)


@router.get("/companies/{symbol}", response_model=CompanyDetailResponse)
async def get_company(
    symbol: str,
    request: Request = None,
    current_user: dict | None = Depends(get_current_user_optional),
):
    _feature_enabled()
    await _apply_rate_limit(request, "markets_company_detail")
    normalized = market_service.normalize_symbol(symbol)
    user_id = current_user["id"] if current_user else None
    cache_key = f"markets:company:{normalized}"
    cached = await redis_get(cache_key)

    await _repository_call(market_repository.upsert_recent_view(user_id, normalized))
    portfolio_position = await _repository_call(market_repository.get_portfolio_position(user_id, normalized))

    if cached:
        detail = CompanyDetailResponse.model_validate(cached)
    else:
        try:
            detail = await market_service.get_company_detail(normalized, portfolio_position=portfolio_position)
        except Exception as exc:
            logger.error(f"Failed to fetch company detail for {normalized}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Company data is temporarily unavailable. The upstream data provider (yfinance) may be throttled or returning errors.",
            )
        await redis_set(cache_key, detail.model_dump(mode="json"), ttl=180)

    return detail.model_copy(update={"portfolioPosition": portfolio_position})


@router.get("/companies/{symbol}/chart", response_model=CompanyChartResponse)
async def get_company_chart(
    symbol: str,
    range_value: ChartRange = Query(..., alias="range"),
    request: Request = None,
):
    _feature_enabled()
    await _apply_rate_limit(request, "markets_company_chart")
    normalized = market_service.normalize_symbol(symbol)
    cache_key = f"markets:chart:{normalized}:{range_value.value}"
    cached = await redis_get(cache_key)
    if cached:
        return cached
    chart = await market_service.get_chart(normalized, range_value)
    await redis_set(cache_key, chart.model_dump(mode="json"), ttl=180)
    return chart


@router.get("/companies/{symbol}/news", response_model=list[EnrichedNewsArticle])
async def get_company_news(
    symbol: str,
    limit: int = Query(10, ge=1, le=30),
    request: Request = None,
    current_user: dict | None = Depends(get_current_user_optional),
):
    _feature_enabled()
    await _apply_rate_limit(request, "markets_company_news")
    normalized = market_service.normalize_symbol(symbol)
    user_id = current_user["id"] if current_user else None
    bookmarks = await _repository_call(market_repository.load_bookmarked_urls(user_id))
    cache_key = f"markets:company_news:{normalized}:{limit}"
    cached = await redis_get(cache_key)
    if cached:
        base_articles = [EnrichedNewsArticle.model_validate(item) for item in cached]
    else:
        base_articles = await market_service.get_company_news(normalized, limit=limit, bookmarked_urls=set())
        await redis_set(cache_key, [item.model_dump(mode="json") for item in base_articles], ttl=180)
    return _with_bookmarks(base_articles, bookmarks)


@router.get("/news", response_model=MarketNewsFeedResponse)
async def list_market_news(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=30),
    category: Optional[str] = None,
    exchange: Optional[str] = None,
    sector: Optional[str] = None,
    market_cap: Optional[str] = Query(None, alias="marketCap"),
    sentiment: Optional[str] = None,
    request: Request = None,
    current_user: dict | None = Depends(get_current_user_optional),
):
    _feature_enabled()
    await _apply_rate_limit(request, "markets_news_feed")
    user_id = current_user["id"] if current_user else None
    bookmarks = await _repository_call(market_repository.load_bookmarked_urls(user_id))
    cache_key = ":".join(
        [
            "markets",
            "news",
            str(page),
            str(limit),
            category or "all",
            exchange or "all",
            sector or "all",
            market_cap or "all",
            sentiment or "all",
        ]
    )
    cached = await redis_get(cache_key)
    if cached:
        response = MarketNewsFeedResponse.model_validate(cached)
    else:
        response = await market_service.get_news_feed(
            page=page,
            limit=limit,
            category=category,
            sentiment=sentiment,
            sector=sector,
            exchange=exchange,
            market_cap=market_cap,
            bookmarked_urls=set(),
        )
        await redis_set(cache_key, response.model_dump(mode="json"), ttl=120)

    return response.model_copy(update={"articles": _with_bookmarks(response.articles, bookmarks)})


@router.get("/watchlist", response_model=list[SearchResult])
async def get_watchlist(
    current_user: dict = Depends(get_current_user),
):
    _feature_enabled()
    symbols = await _repository_call(market_repository.load_watchlist_symbols(current_user["id"]))
    return [quote.model_dump(mode="json") for quote in await market_service.get_quotes(symbols)]


@router.post("/watchlist", response_model=MutationResponse)
async def add_watchlist(
    payload: MarketWatchlistEntry,
    current_user: dict = Depends(get_current_user),
):
    _feature_enabled()
    symbol = market_service.normalize_symbol(payload.symbol)
    await _repository_call(
        market_repository.upsert_watchlist(
            current_user["id"],
            symbol=symbol,
            exchange=payload.exchange,
            notes=payload.notes,
        )
    )
    return MutationResponse(message=f"{symbol} added to Market Pulse watchlist")


@router.delete("/watchlist/{symbol}", response_model=MutationResponse)
async def delete_watchlist(
    symbol: str,
    current_user: dict = Depends(get_current_user),
):
    _feature_enabled()
    normalized = market_service.normalize_symbol(symbol)
    await _repository_call(market_repository.delete_watchlist(current_user["id"], normalized))
    return MutationResponse(message=f"{normalized} removed from Market Pulse watchlist")


@router.get("/bookmarks", response_model=list[BookmarkRecord])
async def get_bookmarks(
    current_user: dict = Depends(get_current_user),
):
    _feature_enabled()
    return await _repository_call(market_repository.list_bookmarks(current_user["id"]))


@router.post("/bookmarks", response_model=MutationResponse)
async def add_bookmark(
    payload: BookmarkCreate,
    current_user: dict = Depends(get_current_user),
):
    _feature_enabled()
    await _repository_call(market_repository.add_bookmark(current_user["id"], payload))
    return MutationResponse(message="Article bookmarked")


@router.delete("/bookmarks/{article_id}", response_model=MutationResponse)
async def delete_bookmark(
    article_id: str,
    current_user: dict = Depends(get_current_user),
):
    _feature_enabled()
    await _repository_call(market_repository.delete_bookmark(current_user["id"], article_id))
    return MutationResponse(message="Bookmark removed")


@router.get("/alerts", response_model=list[PriceAlertResponse])
async def list_alerts(
    current_user: dict = Depends(get_current_user),
):
    _feature_enabled()
    return await _repository_call(market_repository.list_alerts(current_user["id"]))


@router.post("/alerts", response_model=MutationResponse)
async def add_alert(
    payload: PriceAlertCreate,
    current_user: dict = Depends(get_current_user),
):
    _feature_enabled()
    normalized = market_service.normalize_symbol(payload.symbol)
    await _repository_call(market_repository.create_alert(current_user["id"], payload, symbol=normalized))
    return MutationResponse(message="Alert created")


@router.delete("/alerts/{alert_id}", response_model=MutationResponse)
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    _feature_enabled()
    await _repository_call(market_repository.delete_alert(current_user["id"], alert_id))
    return MutationResponse(message="Alert removed")


@router.websocket("/ws")
async def markets_ws(websocket: WebSocket):
    if not settings.FEATURE_MARKETS:
        await websocket.close(code=1008, reason="Markets module disabled")
        return

    await websocket.accept()
    symbols: set[str] = set()
    await websocket.send_json(MarketSocketMessage(type="heartbeat", message="connected").model_dump(mode="json"))

    try:
        while True:
            try:
                incoming = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                action = incoming.get("action")
                requested = [
                    market_service.normalize_symbol(symbol)
                    for symbol in incoming.get("symbols", [])
                    if isinstance(symbol, str)
                ]
                if action == "subscribe":
                    symbols.update(requested)
                    await websocket.send_json(
                        MarketSocketMessage(
                            type="subscribed",
                            symbols=sorted(symbols),
                            message="subscription updated",
                        ).model_dump(mode="json")
                    )
                elif action == "unsubscribe":
                    symbols.difference_update(requested)
                    await websocket.send_json(
                        MarketSocketMessage(
                            type="unsubscribed",
                            symbols=sorted(symbols),
                            message="subscription updated",
                        ).model_dump(mode="json")
                    )
                else:
                    await websocket.send_json(
                        MarketSocketMessage(type="error", message="Unsupported websocket action").model_dump(mode="json")
                    )
            except asyncio.TimeoutError:
                try:
                    if not symbols:
                        await websocket.send_json(
                            MarketSocketMessage(type="heartbeat", message="idle").model_dump(mode="json")
                        )
                        continue
                    quotes = await market_service.get_quotes(sorted(symbols))
                    await websocket.send_json(
                        MarketSocketMessage(
                            type="quote_update",
                            symbols=[quote.displaySymbol for quote in quotes],
                            quotes=quotes,
                        ).model_dump(mode="json")
                    )
                except (WebSocketDisconnect, RuntimeError, ConnectionError, websockets.exceptions.ConnectionClosed):
                    break
            except (WebSocketDisconnect, RuntimeError, ConnectionError, websockets.exceptions.ConnectionClosed):
                break
    except Exception as exc:
        # Don't log normal disconnects as errors
        if not isinstance(exc, (WebSocketDisconnect, websockets.exceptions.ConnectionClosed)):
            logger.debug(f"Market websocket closing: {exc}")
    finally:
        logger.info("Market websocket connection closed")
