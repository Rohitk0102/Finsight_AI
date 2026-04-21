from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes import markets as market_routes
from app.schemas.markets import (
    AnalystConsensus,
    ChartRange,
    CompanyChartResponse,
    CompanyDetailResponse,
    KeyStats,
    MarketOverviewResponse,
    MarketStatus,
    MutationResponse,
    PriceSnapshot,
    SearchContextResponse,
    SearchResult,
    SymbolIdentity,
)


def _request() -> SimpleNamespace:
    return SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))


def _quote(symbol: str = "RELIANCE") -> PriceSnapshot:
    return PriceSnapshot(
        symbol=f"{symbol}.NS",
        displaySymbol=symbol,
        exchange="NSE",
        companyName=f"{symbol} Industries",
        logoUrl=None,
        sector="Energy",
        currentPrice=2840.0,
        change=12.4,
        changePct=0.44,
        marketStatus=MarketStatus.LIVE,
        lastUpdated=datetime.now(timezone.utc),
        volume=100,
        previousClose=2827.6,
    )


@pytest.mark.asyncio
async def test_markets_search_uses_cache(monkeypatch):
    cached = [{"displaySymbol": "RELIANCE"}]

    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def cache_get(*_args, **_kwargs):
        return cached

    monkeypatch.setattr(market_routes, "_apply_rate_limit", no_rate_limit)
    monkeypatch.setattr(market_routes, "redis_get", cache_get)

    result = await market_routes.search_markets(q="reliance", request=_request())
    assert result == cached


@pytest.mark.asyncio
async def test_markets_search_context_loads_recent(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def load_recent(*_args, **_kwargs):
        return ["RELIANCE", "TCS"]

    async def fake_context(symbols):
        assert symbols == ["RELIANCE", "TCS"]
        return SearchContextResponse(
            recent=[
                SymbolIdentity(
                    symbol="RELIANCE.NS",
                    displaySymbol="RELIANCE",
                    exchange="NSE",
                    companyName="Reliance Industries",
                    sector="Energy",
                )
            ],
            trending=[_quote("RELIANCE")],
        )

    monkeypatch.setattr(market_routes, "_apply_rate_limit", no_rate_limit)
    monkeypatch.setattr(market_routes.market_repository, "load_recent_symbols", load_recent)
    monkeypatch.setattr(market_routes.market_service, "get_search_context", fake_context)

    result = await market_routes.search_context(request=_request(), current_user={"id": "user_1"})
    assert result.recent[0].displaySymbol == "RELIANCE"


@pytest.mark.asyncio
async def test_company_detail_records_recent_view(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    recorded = {"symbol": None}

    async def upsert_recent(_user_id, symbol):
        recorded["symbol"] = symbol

    async def fake_company_detail(*_args, **_kwargs):
        return CompanyDetailResponse(
            profile=_quote(),
            stats=KeyStats(),
            analystConsensus=AnalystConsensus(rating="Buy", buy=8, hold=2, sell=1, targetPrice=3000.0),
            peers=[],
            financials={"quarterly": [], "annual": []},
            shareholding=[],
            portfolioPosition=None,
        )

    monkeypatch.setattr(market_routes, "_apply_rate_limit", no_rate_limit)
    monkeypatch.setattr(market_routes.market_repository, "upsert_recent_view", upsert_recent)
    async def fake_portfolio(*_args, **_kwargs):
        return None

    monkeypatch.setattr(market_routes.market_repository, "get_portfolio_position", fake_portfolio)
    async def cache_get(*_args, **_kwargs):
        return None

    async def cache_set(*_args, **_kwargs):
        return None

    monkeypatch.setattr(market_routes, "redis_get", cache_get)
    monkeypatch.setattr(market_routes, "redis_set", cache_set)
    monkeypatch.setattr(market_routes.market_service, "get_company_detail", fake_company_detail)

    await market_routes.get_company("reliance", request=_request(), current_user={"id": "user_1"})
    assert recorded["symbol"] == "RELIANCE"


@pytest.mark.asyncio
async def test_markets_feature_flag_blocks_routes(monkeypatch):
    monkeypatch.setattr(market_routes.settings, "FEATURE_MARKETS", False)
    with pytest.raises(HTTPException) as exc_info:
        await market_routes.search_markets(q="reliance", request=_request())
    assert exc_info.value.status_code == 404
    monkeypatch.setattr(market_routes.settings, "FEATURE_MARKETS", True)


@pytest.mark.asyncio
async def test_markets_chart_route_passes_range(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    captured = {"range": None}

    async def fake_chart(symbol, range_value):
        captured["range"] = range_value
        return CompanyChartResponse(symbol=symbol.upper(), range=range_value, points=[])

    monkeypatch.setattr(market_routes, "_apply_rate_limit", no_rate_limit)
    async def cache_get(*_args, **_kwargs):
        return None

    async def cache_set(*_args, **_kwargs):
        return None

    monkeypatch.setattr(market_routes, "redis_get", cache_get)
    monkeypatch.setattr(market_routes, "redis_set", cache_set)
    monkeypatch.setattr(market_routes.market_service, "get_chart", fake_chart)
    result = await market_routes.get_company_chart("infy", range_value=ChartRange.Y1, request=_request())
    assert result.range == ChartRange.Y1
    assert captured["range"] == ChartRange.Y1


@pytest.mark.asyncio
async def test_watchlist_add_uses_upsert(monkeypatch):
    captured = {"payload": None}

    async def fake_upsert(*_args, **_kwargs):
        captured["payload"] = "market_watchlist_upsert"

    monkeypatch.setattr(market_routes.market_repository, "upsert_watchlist", fake_upsert)

    response = await market_routes.add_watchlist(
        market_routes.MarketWatchlistEntry(symbol="reliance", exchange="NSE"),
        current_user={"id": "user_1"},
    )
    assert response.message.endswith("added to Market Pulse watchlist")
    assert captured["payload"] == "market_watchlist_upsert"


@pytest.mark.asyncio
async def test_overview_includes_personalization(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def load_watchlist(*_args, **_kwargs):
        return ["RELIANCE"]

    async def load_bookmarks(*_args, **_kwargs):
        return {"https://example.com/story"}

    async def fake_overview(symbols, bookmarks):
        assert symbols == ["RELIANCE"]
        assert "https://example.com/story" in bookmarks
        return MarketOverviewResponse(
            marketStatus=MarketStatus.LIVE,
            indices=[],
            watchlist=[_quote()],
            topGainers=[],
            topLosers=[],
            mostActive=[],
            sectorHeatmap=[],
            fiiDiiActivity={"sessionDate": "2026-04-18", "fiiNet": 1, "diiNet": -1},
            ipoTracker=[],
            economicCalendar=[],
            latestNews=[],
            breakingNewsCount=1,
        )

    monkeypatch.setattr(market_routes, "_apply_rate_limit", no_rate_limit)
    monkeypatch.setattr(market_routes.market_repository, "load_watchlist_symbols", load_watchlist)
    monkeypatch.setattr(market_routes.market_repository, "load_bookmarked_urls", load_bookmarks)
    async def cache_get(*_args, **_kwargs):
        return None

    async def cache_set(*_args, **_kwargs):
        return None

    monkeypatch.setattr(market_routes, "redis_get", cache_get)
    monkeypatch.setattr(market_routes, "redis_set", cache_set)
    monkeypatch.setattr(market_routes.market_service, "get_overview", fake_overview)

    result = await market_routes.get_overview(request=_request(), current_user={"id": "user_1"})
    assert result.breakingNewsCount == 1
