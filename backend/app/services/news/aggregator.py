"""
News Aggregator Service: Multi-source news fetching with normalization and deduplication.

This service fetches financial news from multiple free-tier APIs (NewsAPI, GNews, Finnhub,
Alpha Vantage, Marketaux) and normalizes them into a unified schema.
"""
from dataclasses import dataclass
import httpx
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Awaitable, Callable, Dict, List, Literal, Optional, Sequence
from app.schemas.news import NewsArticle, NewsCategory, SentimentLabel
from app.core.config import settings
from loguru import logger


def _to_utc(dt: datetime) -> datetime:
    """Ensure datetime is UTC-aware; assumes naive datetimes are UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class SourceFetchResult:
    source: str
    articles: List[NewsArticle]
    status: Literal["success", "empty", "failed", "skipped"]
    error: Optional[str] = None


@dataclass(frozen=True)
class AggregationResult:
    articles: List[NewsArticle]
    attempted_sources: tuple[str, ...]
    successful_sources: tuple[str, ...]
    empty_sources: tuple[str, ...]
    failed_sources: tuple[str, ...]
    skipped_sources: tuple[str, ...]


class NewsAggregator:
    """Fetch and normalize news from multiple sources"""
    
    def __init__(self):
        """Initialize aggregator with source mapping"""
        self.title_similarity_threshold = 0.85
        self.verify_ssl = settings.ENVIRONMENT != "development"
        self.sources: Dict[str, Callable[[str, int], Awaitable[List[NewsArticle]]]] = {
            'newsapi': self._fetch_newsapi,
            'gnews': self._fetch_gnews,
            'finnhub': self._fetch_finnhub,
            'alpha_vantage': self._fetch_alpha_vantage,
            'marketaux': self._fetch_marketaux,
            'fmp': self._fetch_fmp,
        }
        self.market_source_names = ("newsapi", "gnews")
        self.ticker_source_names = tuple(self.sources.keys())
    
    async def aggregate_all_sources(
        self,
        query: str,
        limit: int = 20
    ) -> List[NewsArticle]:
        """
        Fetch from all sources in parallel and combine results.
        
        Args:
            query: Search query (company name or ticker)
            limit: Maximum number of articles to return
            
        Returns:
            List of normalized and deduplicated articles
        """
        result = await self.aggregate_ticker_sources(query=query, limit=limit)
        return result.articles

    async def aggregate_market_sources(self, query: str, limit: int = 20) -> AggregationResult:
        """Fetch market-wide news only from providers that support keyword search."""
        return await self._aggregate_sources(self.market_source_names, query=query, limit=limit)

    async def aggregate_ticker_sources(self, query: str, limit: int = 20) -> AggregationResult:
        """Fetch ticker-scoped news using the full provider set."""
        return await self._aggregate_sources(self.ticker_source_names, query=query, limit=limit)

    async def _aggregate_sources(
        self,
        source_names: Sequence[str],
        *,
        query: str,
        limit: int,
    ) -> AggregationResult:
        selected_sources = tuple(source_names)
        attempted_sources = tuple(
            source_name for source_name in selected_sources if self._is_source_enabled(source_name)
        )
        skipped_sources = tuple(
            source_name for source_name in selected_sources if source_name not in attempted_sources
        )

        if not attempted_sources:
            logger.warning("No enabled news providers available for query: {}", query)
            return AggregationResult(
                articles=[],
                attempted_sources=(),
                successful_sources=(),
                empty_sources=(),
                failed_sources=(),
                skipped_sources=skipped_sources,
            )

        tasks = [self._run_source(source_name, query=query, limit=limit) for source_name in attempted_sources]
        results = await asyncio.gather(*tasks)

        articles: List[NewsArticle] = []
        successful_sources: List[str] = []
        empty_sources: List[str] = []
        failed_sources: List[str] = []

        for result in results:
            if result.status == "failed":
                failed_sources.append(result.source)
                continue
            if result.status == "empty":
                empty_sources.append(result.source)
                continue
            successful_sources.append(result.source)
            articles.extend(result.articles)

        deduplicated = self.deduplicate_articles(articles)
        return AggregationResult(
            articles=deduplicated[:limit],
            attempted_sources=attempted_sources,
            successful_sources=tuple(successful_sources),
            empty_sources=tuple(empty_sources),
            failed_sources=tuple(failed_sources),
            skipped_sources=skipped_sources,
        )

    async def _run_source(self, source_name: str, *, query: str, limit: int) -> SourceFetchResult:
        fetch_func = self.sources[source_name]

        try:
            articles = await fetch_func(query, limit)
        except httpx.TimeoutException as exc:
            logger.warning("Timeout fetching from {}: {}", source_name, exc)
            return SourceFetchResult(
                source=source_name,
                articles=[],
                status="failed",
                error=f"Timeout: {str(exc)}",
            )
        except httpx.HTTPStatusError as exc:
            logger.warning("HTTP error fetching from {} (status {}): {}", source_name, exc.response.status_code, exc)
            return SourceFetchResult(
                source=source_name,
                articles=[],
                status="failed",
                error=f"HTTP {exc.response.status_code}",
            )
        except Exception as exc:
            logger.error("Unexpected error fetching from {}: {}", source_name, exc)
            return SourceFetchResult(
                source=source_name,
                articles=[],
                status="failed",
                error=str(exc),
            )

        status: Literal["success", "empty", "failed", "skipped"] = "success" if articles else "empty"
        return SourceFetchResult(source=source_name, articles=articles, status=status)

    def _is_source_enabled(self, source_name: str) -> bool:
        source_keys = {
            "newsapi": settings.NEWS_API_KEY,
            "gnews": settings.GNEWS_API_KEY,
            "finnhub": settings.FINNHUB_API_KEY,
            "alpha_vantage": settings.ALPHA_VANTAGE_API_KEY,
            "marketaux": settings.MARKETAUX_API_KEY,
            "fmp": settings.FMP_API_KEY,
        }
        return bool(source_keys.get(source_name))
    
    async def _fetch_newsapi(self, query: str, limit: int) -> List[NewsArticle]:
        """
        Fetch from NewsAPI with India filter.
        
        Rate Limit: 100 requests/day (free tier)
        """
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": f"{query} India",  # Add India filter as per requirement 1.2
            "from": (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d"),
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(limit, 100),
            "apiKey": settings.NEWS_API_KEY
        }
        
        async with httpx.AsyncClient(timeout=10, verify=self.verify_ssl) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Check for API error responses
        if data.get("status") == "error":
            error_code = data.get("code", "unknown")
            error_message = data.get("message", "Unknown error")
            raise RuntimeError(f"NewsAPI error ({error_code}): {error_message}")

        articles = []
        for article in data.get("articles", []):
            # Skip removed articles
            if article.get("title") == "[Removed]":
                continue

            normalized = self._normalize_newsapi_article(article)
            if normalized:
                articles.append(normalized)

        logger.info(f"Fetched {len(articles)} articles from NewsAPI for query: {query}")
        return articles
    
    async def _fetch_gnews(self, query: str, limit: int) -> List[NewsArticle]:
        """
        Fetch from GNews API with proper parameter mapping.
        
        Rate Limit: 100 requests/day (free tier)
        """
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": f"{query} India",  # Add India filter
            "lang": "en",
            "country": "in",  # India country filter
            "max": min(limit, 10),  # GNews free tier max is 10
            "apikey": settings.GNEWS_API_KEY
        }
        
        async with httpx.AsyncClient(timeout=10, verify=self.verify_ssl) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Check for API error responses
        if "errors" in data:
            errors = data.get("errors", [])
            raise RuntimeError(f"GNews API error: {errors}")

        articles = []
        for article in data.get("articles", []):
            normalized = self._normalize_gnews_article(article)
            if normalized:
                articles.append(normalized)

        logger.info(f"Fetched {len(articles)} articles from GNews for query: {query}")
        return articles
    
    async def _fetch_finnhub(self, query: str, limit: int) -> List[NewsArticle]:
        """
        Fetch from Finnhub API with ticker-based queries.
        
        Rate Limit: 60 calls/minute (free tier)
        """
        # Finnhub requires ticker symbol, try to use query as ticker
        url = "https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": query.upper(),
            "from": (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d"),
            "to": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "token": settings.FINNHUB_API_KEY
        }
        
        async with httpx.AsyncClient(timeout=10, verify=self.verify_ssl) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Check for API error responses
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"Finnhub API error: {data.get('error')}")

        articles = []
        items = data[:limit] if isinstance(data, list) else []

        for article in items:
            normalized = self._normalize_finnhub_article(article, query)
            if normalized:
                articles.append(normalized)

        logger.info(f"Fetched {len(articles)} articles from Finnhub for query: {query}")
        return articles
    
    async def _fetch_alpha_vantage(self, query: str, limit: int) -> List[NewsArticle]:
        """
        Fetch from Alpha Vantage news sentiment endpoint.
        
        Rate Limit: 25 requests/day (free tier)
        """
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": query.upper(),
            "apikey": settings.ALPHA_VANTAGE_API_KEY,
            "limit": min(limit, 50)
        }
        
        async with httpx.AsyncClient(timeout=10, verify=self.verify_ssl) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Check for API error responses (rate limit, invalid key, etc.)
        if "Error Message" in data or "Note" in data:
            error_msg = data.get("Error Message") or data.get("Note", "Unknown error")
            raise RuntimeError(f"Alpha Vantage API error: {error_msg}")

        articles = []
        for article in data.get("feed", []):
            normalized = self._normalize_alpha_vantage_article(article, query)
            if normalized:
                articles.append(normalized)

        logger.info(f"Fetched {len(articles)} articles from Alpha Vantage for query: {query}")
        return articles
    
    async def _fetch_marketaux(self, query: str, limit: int) -> List[NewsArticle]:
        """
        Fetch from Marketaux API with India market filter.
        
        Rate Limit: 100 requests/day (free tier)
        """
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            "symbols": query.upper(),
            "filter_entities": "true",
            "language": "en",
            "countries": "in",  # India filter
            "limit": min(limit, 100),
            "api_token": settings.MARKETAUX_API_KEY
        }
        
        async with httpx.AsyncClient(timeout=10, verify=self.verify_ssl) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Check for API error responses
        if "error" in data:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            raise RuntimeError(f"Marketaux API error: {error_msg}")

        articles = []
        for article in data.get("data", []):
            normalized = self._normalize_marketaux_article(article, query)
            if normalized:
                articles.append(normalized)

        logger.info(f"Fetched {len(articles)} articles from Marketaux for query: {query}")
        return articles

    async def _fetch_fmp(self, query: str, limit: int) -> List[NewsArticle]:
        """
        Fetch from Financial Modeling Prep (FMP) stock news endpoint.
        """
        url = "https://financialmodelingprep.com/api/v3/stock_news"
        params = {
            "tickers": query.upper(),
            "limit": limit,
            "apikey": settings.FMP_API_KEY
        }
        
        async with httpx.AsyncClient(timeout=10, verify=self.verify_ssl) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if isinstance(data, dict) and "Error Message" in data:
            raise RuntimeError(f"FMP API error: {data.get('Error Message')}")

        articles = []
        if not isinstance(data, list):
            return []
            
        for article in data:
            normalized = self._normalize_fmp_article(article, query)
            if normalized:
                articles.append(normalized)

        logger.info(f"Fetched {len(articles)} articles from FMP for query: {query}")
        return articles
    
    def _normalize_newsapi_article(self, raw: Dict) -> Optional[NewsArticle]:
        """Convert NewsAPI response to unified schema"""
        try:
            # Validate required fields
            if not all([raw.get("title"), raw.get("url"), raw.get("publishedAt")]):
                return None
            
            return NewsArticle(
                id=str(uuid.uuid4()),
                ticker=None,  # Will be enriched later
                title=raw.get("title", ""),
                description=raw.get("description") or raw.get("content", "")[:500],
                url=raw.get("url", ""),
                source=raw.get("source", {}).get("name", "NewsAPI"),
                published_at=_to_utc(datetime.fromisoformat(
                    raw["publishedAt"].replace("Z", "+00:00")
                )),
                image_url=raw.get("urlToImage"),
                related_tickers=[],
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0,
                impact_prediction=None,
                created_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Error normalizing NewsAPI article: {e}")
            return None

    def _normalize_gnews_article(self, raw: Dict) -> Optional[NewsArticle]:
        """Convert GNews response to unified schema"""
        try:
            # Validate required fields
            if not all([raw.get("title"), raw.get("url"), raw.get("publishedAt")]):
                return None
            
            return NewsArticle(
                id=str(uuid.uuid4()),
                ticker=None,
                title=raw.get("title", ""),
                description=raw.get("description", ""),
                url=raw.get("url", ""),
                source=raw.get("source", {}).get("name", "GNews"),
                published_at=_to_utc(datetime.fromisoformat(
                    raw["publishedAt"].replace("Z", "+00:00")
                )),
                image_url=raw.get("image"),
                related_tickers=[],
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0,
                impact_prediction=None,
                created_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Error normalizing GNews article: {e}")
            return None
    
    def _normalize_finnhub_article(self, raw: Dict, ticker: str) -> Optional[NewsArticle]:
        """Convert Finnhub response to unified schema"""
        try:
            # Validate required fields
            if not all([raw.get("headline"), raw.get("url"), raw.get("datetime")]):
                return None
            
            return NewsArticle(
                id=str(raw.get("id", uuid.uuid4())),
                ticker=ticker.upper(),
                title=raw.get("headline", ""),
                description=raw.get("summary", ""),
                url=raw.get("url", ""),
                source=raw.get("source", "Finnhub"),
                published_at=datetime.fromtimestamp(
                    raw.get("datetime", 0),
                    tz=timezone.utc
                ),
                image_url=raw.get("image"),
                related_tickers=[ticker.upper()],
                category=self._classify_category(raw.get("category", "")),
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0,
                impact_prediction=None,
                created_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Error normalizing Finnhub article: {e}")
            return None
    
    def _normalize_alpha_vantage_article(self, raw: Dict, ticker: str) -> Optional[NewsArticle]:
        """Convert Alpha Vantage response to unified schema"""
        try:
            # Validate required fields
            if not all([raw.get("title"), raw.get("url"), raw.get("time_published")]):
                return None
            
            # Parse Alpha Vantage timestamp format: YYYYMMDDTHHMMSS
            time_str = raw.get("time_published", "")
            published_at = datetime.strptime(time_str, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            
            return NewsArticle(
                id=str(uuid.uuid4()),
                ticker=ticker.upper(),
                title=raw.get("title", ""),
                description=raw.get("summary", ""),
                url=raw.get("url", ""),
                source=raw.get("source", "Alpha Vantage"),
                published_at=published_at,
                image_url=raw.get("banner_image"),
                related_tickers=[ticker.upper()],
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0,
                impact_prediction=None,
                created_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Error normalizing Alpha Vantage article: {e}")
            return None
    
    def _normalize_marketaux_article(self, raw: Dict, ticker: str) -> Optional[NewsArticle]:
        """Convert Marketaux response to unified schema"""
        try:
            # Validate required fields
            if not all([raw.get("title"), raw.get("url"), raw.get("published_at")]):
                return None
            
            return NewsArticle(
                id=str(raw.get("uuid", uuid.uuid4())),
                ticker=ticker.upper(),
                title=raw.get("title", ""),
                description=raw.get("description", ""),
                url=raw.get("url", ""),
                source=raw.get("source", "Marketaux"),
                published_at=_to_utc(datetime.fromisoformat(
                    raw["published_at"].replace("Z", "+00:00")
                )),
                image_url=raw.get("image_url"),
                related_tickers=[ticker.upper()],
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0,
                impact_prediction=None,
                created_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Error normalizing Marketaux article: {e}")
            return None

    def _normalize_fmp_article(self, raw: Dict, ticker: str) -> Optional[NewsArticle]:
        """Convert FMP response to unified schema"""
        try:
            # Validate required fields
            if not all([raw.get("title"), raw.get("url"), raw.get("publishedDate")]):
                return None
            
            # FMP publishedDate format: 2024-03-21 12:00:00
            pub_date_str = raw.get("publishedDate", "")
            try:
                published_at = _to_utc(datetime.fromisoformat(pub_date_str))
            except ValueError:
                published_at = _to_utc(datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S"))

            return NewsArticle(
                id=str(uuid.uuid4()),
                ticker=ticker.upper(),
                title=raw.get("title", ""),
                description=raw.get("text", ""),
                url=raw.get("url", ""),
                source=raw.get("site", "Financial Modeling Prep"),
                published_at=published_at,
                image_url=raw.get("image"),
                related_tickers=[ticker.upper()],
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0,
                impact_prediction=None,
                created_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Error normalizing FMP article: {e}")
            return None
    
    def deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Remove duplicate articles by URL and title similarity.
        
        Args:
            articles: List of articles to deduplicate
            
        Returns:
            List of unique articles
        """
        seen_urls = set()
        unique = []
        
        for article in articles:
            # Skip if URL already seen
            if article.url in seen_urls:
                continue
            
            # Check title similarity with existing articles
            is_duplicate = False
            for existing in unique:
                similarity = self._calculate_similarity(
                    article.title,
                    existing.title
                )
                if similarity >= self.title_similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_urls.add(article.url)
                unique.append(article)
        
        return unique
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity between two strings.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _classify_category(self, raw: str) -> NewsCategory:
        """Classify news category from raw string"""
        mapping = {
            "earnings": NewsCategory.EARNINGS,
            "merger": NewsCategory.MERGER,
            "macro": NewsCategory.MACRO,
            "regulatory": NewsCategory.REGULATORY,
            "insider": NewsCategory.INSIDER,
        }
        return mapping.get(raw.lower(), NewsCategory.GENERAL)
