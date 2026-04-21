from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.schemas.markets import (
    ChartRange,
    CompanyDetailResponse,
    MarketMover,
    MarketNewsFeedResponse,
    MarketOverviewResponse,
    MarketStatus,
    PriceSnapshot,
    SearchContextResponse,
    SearchResult,
    SymbolIdentity,
)
from app.services.markets.providers import (
    ClaudeImpactAnalyzer,
    DefaultMarketDataProvider,
    DefaultMarketNewsProvider,
    GeminiImpactAnalyzer,
    HuggingFaceImpactAnalyzer,
    HeuristicImpactAnalyzer,
    StaticMarketCalendarProvider,
    StaticMarketIpoProvider,
    compute_market_status,
)


class MarketPulseService:
    def __init__(self) -> None:
        self.data_provider = DefaultMarketDataProvider()
        self.news_provider = DefaultMarketNewsProvider()
        heuristic = HeuristicImpactAnalyzer(self.data_provider)
        huggingface = HuggingFaceImpactAnalyzer(heuristic)
        gemini = GeminiImpactAnalyzer(huggingface)
        self.impact_analyzer = ClaudeImpactAnalyzer(gemini)
        self.calendar_provider = StaticMarketCalendarProvider()
        self.ipo_provider = StaticMarketIpoProvider()

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace(".NS", "").replace(".BO", "")

    async def _gather_quotes(self, symbols: list[str], *, limit: Optional[int] = None) -> list[PriceSnapshot]:
        cleaned = [self.normalize_symbol(symbol) for symbol in symbols if symbol]
        deduped = list(dict.fromkeys(cleaned))
        if limit is not None:
            deduped = deduped[:limit]
        if not deduped:
            return []
        quotes = await asyncio.gather(*[self.data_provider.get_quote(symbol) for symbol in deduped], return_exceptions=True)
        return [quote for quote in quotes if isinstance(quote, PriceSnapshot)]

    async def _build_company_context(self, symbols: set[str]) -> dict[str, dict[str, Optional[str]]]:
        if not symbols:
            return {}

        async def fetch(symbol: str):
            quote, stats = await self.data_provider.get_company_profile(symbol)
            return {
                "symbol": quote.displaySymbol,
                "exchange": quote.exchange.upper(),
                "sector": (quote.sector or "").lower(),
                "marketCapBucket": self.data_provider._market_cap_bucket(stats.marketCap),
            }

        resolved = await asyncio.gather(*[fetch(symbol) for symbol in sorted(symbols)], return_exceptions=True)
        context: dict[str, dict[str, Optional[str]]] = {}
        for item in resolved:
            if isinstance(item, dict):
                context[item["symbol"]] = item
        return context

    def _article_matches_filters(
        self,
        *,
        article,
        company_context: dict[str, dict[str, Optional[str]]],
        sentiment: Optional[str],
        sector: Optional[str],
        exchange: Optional[str],
        market_cap: Optional[str],
    ) -> bool:
        if sentiment and article.sentimentLabel.value != sentiment.lower():
            return False

        company_symbols = list(
            dict.fromkeys(
                [
                    article.primarySymbol,
                    *[company.displaySymbol for company in article.affectedCompanies],
                ]
            )
        )
        matched_context = [company_context[symbol] for symbol in company_symbols if symbol and symbol in company_context]

        if sector:
            sector_match = any(item.get("sector") == sector.lower() for item in matched_context)
            ripple_match = any(ripple.sector.lower() == sector.lower() for ripple in article.sectorRipple)
            if not sector_match and not ripple_match:
                return False

        if exchange:
            if not any(item.get("exchange") == exchange.upper() for item in matched_context):
                return False

        if market_cap:
            if not any(item.get("marketCapBucket") == market_cap.lower() for item in matched_context):
                return False

        return True

    async def search(self, query: str) -> list[SearchResult]:
        return await self.data_provider.search(query)

    async def get_search_context(self, recent_symbols: list[str]) -> SearchContextResponse:
        recent_quotes, trending = await asyncio.gather(
            self._gather_quotes(recent_symbols, limit=5),
            self._gather_quotes(["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"], limit=5),
        )
        recent = [
            SymbolIdentity(
                symbol=quote.symbol,
                displaySymbol=quote.displaySymbol,
                exchange=quote.exchange,
                companyName=quote.companyName,
                logoUrl=quote.logoUrl,
                sector=quote.sector,
            )
            for quote in recent_quotes
        ]
        return SearchContextResponse(recent=recent, trending=trending)

    async def get_overview(
        self,
        watchlist_symbols: list[str],
        bookmarked_urls: Optional[set[str]] = None,
    ) -> MarketOverviewResponse:
        bookmarked_urls = bookmarked_urls or set()
        
        # News provider might be unavailable; don't let it crash the whole overview.
        async def safe_news_fetch():
            try:
                return await self.news_provider.get_market_news(limit=8, category="market_analysis")
            except Exception as exc:
                logger.warning(f"Overview news fetch failed: {exc}")
                return []

        (
            indices,
            market_lists,
            watchlist,
            fii_dii,
            ipo_tracker,
            calendar,
            market_news,
        ) = await asyncio.gather(
            self.data_provider.get_indices(),
            self.data_provider.get_market_lists(),
            self._gather_quotes(watchlist_symbols, limit=6),
            self.get_fii_dii_activity(),
            self.ipo_provider.list_ipos(),
            self.calendar_provider.list_events(),
            safe_news_fetch(),
        )

        top_gainers, top_losers, most_active, heatmap = market_lists

        # Parallel analysis with a strict timeout per article to keep things fast
        async def analyze_with_timeout(article):
            try:
                # 4 second limit for AI analysis in overview
                return await asyncio.wait_for(
                    self.impact_analyzer.analyze(article, None, []),
                    timeout=4.0
                )
            except Exception:
                # Fallback to a dummy enriched article if AI is too slow
                from app.schemas.markets import EnrichedNewsArticle, SentimentBadge
                return EnrichedNewsArticle(
                    id=article.id,
                    title=article.title,
                    description=article.description,
                    source=article.source,
                    sourceUrl=article.url,
                    publishedAt=article.published_at,
                    imageUrl=article.image_url,
                    category=article.category.value,
                    impactScore=50,
                    sentimentLabel=SentimentBadge.NEUTRAL,
                    aiSummary="Analysis temporarily unavailable...",
                    primarySymbol=article.ticker
                )

        analyzed_news = await asyncio.gather(
            *[analyze_with_timeout(article) for article in market_news[:6]],
            return_exceptions=True,
        )
        latest_news = []
        for item in analyzed_news:
            if not isinstance(item, Exception):
                latest_news.append(
                    item.model_copy(update={"bookmarked": item.sourceUrl in bookmarked_urls})
                    if item.sourceUrl in bookmarked_urls
                    else item
                )

        breaking_count = sum(
            1
            for article in latest_news
            if article.impactScore >= 70
            and article.publishedAt >= datetime.now(timezone.utc) - timedelta(hours=4)
        )

        return MarketOverviewResponse(
            marketStatus=compute_market_status(),
            indices=indices,
            watchlist=watchlist,
            topGainers=top_gainers,
            topLosers=top_losers,
            mostActive=most_active,
            sectorHeatmap=heatmap,
            fiiDiiActivity=fii_dii,
            ipoTracker=ipo_tracker,
            economicCalendar=calendar,
            latestNews=latest_news,
            breakingNewsCount=breaking_count,
        )

    async def get_fii_dii_activity(self):
        today = datetime.now(timezone.utc).date().isoformat()
        status = compute_market_status()
        sign = 1 if status in {MarketStatus.LIVE, MarketStatus.PRE_MARKET} else -1
        return self._fii_dii_payload(today, sign)

    def _fii_dii_payload(self, today: str, sign: int):
        from app.schemas.markets import FiiDiiActivity

        return FiiDiiActivity(
            sessionDate=today,
            fiiNet=round(2143.6 * sign, 2),
            diiNet=round(-1742.2 * sign, 2),
        )

    async def get_company_detail(self, symbol: str, portfolio_position=None) -> CompanyDetailResponse:
        quote_and_stats, analyst, peers, financials, shareholding = await asyncio.gather(
            self.data_provider.get_company_profile(symbol),
            self.data_provider.get_analyst_consensus(symbol),
            self.data_provider.get_peers(symbol),
            self.data_provider.get_financials(symbol),
            self.data_provider.get_shareholding(symbol),
        )
        quote, stats = quote_and_stats
        return CompanyDetailResponse(
            profile=quote,
            stats=stats,
            analystConsensus=analyst,
            peers=peers,
            financials=financials,
            shareholding=shareholding,
            portfolioPosition=portfolio_position,
        )

    async def get_company_news(
        self,
        symbol: str,
        limit: int = 10,
        bookmarked_urls: Optional[set[str]] = None,
    ) -> list:
        bookmarked_urls = bookmarked_urls or set()
        normalized = self.normalize_symbol(symbol)
        
        try:
            (quote, _), peer_items, articles = await asyncio.gather(
                self.data_provider.get_company_profile(normalized),
                self.data_provider.get_peers(normalized),
                self.news_provider.get_company_news(normalized, limit=limit),
            )
        except Exception as exc:
            logger.error(f"Company news fetch failed for {normalized}: {exc}")
            # Try to at least return the profile if news fails, but for simplicity returning empty
            return []
        primary = SymbolIdentity(
            symbol=quote.symbol,
            displaySymbol=quote.displaySymbol,
            exchange=quote.exchange,
            companyName=quote.companyName,
            logoUrl=quote.logoUrl,
            sector=quote.sector,
        )
        peers = [
            SymbolIdentity(
                symbol=peer.symbol,
                displaySymbol=peer.displaySymbol,
                exchange="NSE",
                companyName=peer.companyName,
                sector=peer.sector,
            )
            for peer in peer_items
        ]
        enriched = await asyncio.gather(
            *[self.impact_analyzer.analyze(article, primary, peers) for article in articles],
            return_exceptions=True,
        )
        return [
            item.model_copy(update={"bookmarked": True}) if item.sourceUrl in bookmarked_urls else item
            for item in enriched
            if not isinstance(item, Exception)
        ]

    async def get_news_feed(
        self,
        *,
        page: int,
        limit: int,
        category: Optional[str],
        sentiment: Optional[str],
        sector: Optional[str],
        exchange: Optional[str],
        market_cap: Optional[str],
        bookmarked_urls: Optional[set[str]] = None,
    ) -> MarketNewsFeedResponse:
        bookmarked_urls = bookmarked_urls or set()
        fetch_limit = max(20, limit * page * 2)
        
        try:
            articles = await self.news_provider.get_market_news(limit=fetch_limit, category=category)
        except Exception as exc:
            logger.error(f"News feed fetch failed: {exc}")
            return MarketNewsFeedResponse(
                articles=[],
                total=0,
                page=page,
                limit=limit,
                hasMore=False,
            )

        enriched_results = await asyncio.gather(
            *[self.impact_analyzer.analyze(article, None, []) for article in articles],
            return_exceptions=True,
        )
        enriched = [item for item in enriched_results if not isinstance(item, Exception)]

        company_context = await self._build_company_context(
            {
                symbol
                for article in enriched
                for symbol in [
                    article.primarySymbol,
                    *[company.displaySymbol for company in article.affectedCompanies],
                ]
                if symbol
            }
        ) if any([sector, exchange, market_cap]) else {}

        filtered = []
        for item in enriched:
            if not self._article_matches_filters(
                article=item,
                company_context=company_context,
                sentiment=sentiment,
                sector=sector,
                exchange=exchange,
                market_cap=market_cap,
            ):
                continue
            if item.sourceUrl in bookmarked_urls:
                item = item.model_copy(update={"bookmarked": True})
            filtered.append(item)

        total = len(filtered)
        start = (page - 1) * limit
        end = start + limit
        page_items = filtered[start:end]
        return MarketNewsFeedResponse(
            articles=page_items,
            total=total,
            page=page,
            limit=limit,
            hasMore=end < total,
        )

    async def get_chart(self, symbol: str, range_value: ChartRange):
        return await self.data_provider.get_chart(symbol, range_value)

    async def get_quotes(self, symbols: list[str]) -> list[PriceSnapshot]:
        if not symbols:
            return []
            
        # Parallelize for speed
        results = await asyncio.gather(
            *[self.data_provider.get_quote(s) for symbol in symbols for s in [symbol]],
            return_exceptions=True
        )
        
        quotes = []
        for res in results:
            if isinstance(res, PriceSnapshot):
                quotes.append(res)
            elif isinstance(res, Exception):
                logger.debug(f"Watchlist quote fetch skipped: {res}")
                
        return quotes
