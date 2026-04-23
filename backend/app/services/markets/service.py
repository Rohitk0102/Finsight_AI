from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.schemas.markets import (
    AnalystConsensus,
    ChartRange,
    CompanyDetailResponse,
    EnrichedNewsArticle,
    FinancialsSnapshot,
    KeyStats,
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

        results = await asyncio.gather(
            self.data_provider.get_indices(),
            self.data_provider.get_market_lists(),
            self._gather_quotes(watchlist_symbols, limit=6),
            self.get_fii_dii_activity(),
            self.ipo_provider.list_ipos(),
            self.calendar_provider.list_events(),
            safe_news_fetch(),
            return_exceptions=True
        )

        # Unpack with error handling
        indices = results[0] if not isinstance(results[0], Exception) else []
        market_lists = results[1] if not isinstance(results[1], Exception) else ([], [], [], [])
        watchlist = results[2] if not isinstance(results[2], Exception) else []
        fii_dii = results[3] if not isinstance(results[3], Exception) else await self.get_fii_dii_activity()
        ipo_tracker = results[4] if not isinstance(results[4], Exception) else []
        calendar = results[5] if not isinstance(results[5], Exception) else []
        market_news = results[6] if not isinstance(results[6], Exception) else []

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
        results = await asyncio.gather(
            self.data_provider.get_company_profile(symbol),
            self.data_provider.get_analyst_consensus(symbol),
            self.data_provider.get_peers(symbol),
            self.data_provider.get_financials(symbol),
            self.data_provider.get_shareholding(symbol),
            return_exceptions=True
        )
        
        # Result mapping with fallback for exceptions
        if not isinstance(results[0], Exception):
            quote, stats, about = results[0]
        else:
            try:
                # One last try for profile if the first one failed
                quote, stats, about = await self.data_provider.get_company_profile(symbol)
            except Exception as exc:
                logger.error(f"Critical failure fetching company profile for {symbol}: {exc}")
                # Ultimate fallback - return a bare snapshot from identity metadata
                identity = self.data_provider.get_symbol_identity(symbol)
                quote = PriceSnapshot(
                    **identity.model_dump(),
                    currentPrice=0, change=0, changePct=0,
                    marketStatus=compute_market_status(),
                    lastUpdated=datetime.now(timezone.utc)
                )
                stats = KeyStats()
                about = CompanyAbout()

        analyst = results[1] if not isinstance(results[1], Exception) else AnalystConsensus(rating="Hold", buy=0, hold=0, sell=0)
        peers = results[2] if not isinstance(results[2], Exception) else []
        financials = results[3] if not isinstance(results[3], Exception) else FinancialsSnapshot()
        shareholding = results[4] if not isinstance(results[4], Exception) else []

        return CompanyDetailResponse(
            profile=quote,
            stats=stats,
            about=about,
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
            # Parallel fetch with exception handling
            fetch_results = await asyncio.gather(
                self.data_provider.get_company_profile(normalized),
                self.data_provider.get_peers(normalized),
                self.news_provider.get_company_news(normalized, limit=limit),
                return_exceptions=True
            )
            
            # Map results with fallbacks
            quote_stats = fetch_results[0] if not isinstance(fetch_results[0], Exception) else await self.data_provider.get_company_profile(normalized)
            peer_items = fetch_results[1] if not isinstance(fetch_results[1], Exception) else []
            articles = fetch_results[2] if not isinstance(fetch_results[2], Exception) else []
            
            quote, _ = quote_stats
        except Exception as exc:
            logger.error(f"Fundamental company news fetch failed for {normalized}: {exc}")
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
        
        # News analysis can also fail or be slow
        enriched_results = await asyncio.gather(
            *[self.impact_analyzer.analyze(article, primary, peers) for article in articles],
            return_exceptions=True,
        )
        return [
            item.model_copy(update={"bookmarked": True}) if item.sourceUrl in bookmarked_urls else item
            for item in enriched_results
            if isinstance(item, EnrichedNewsArticle)
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
