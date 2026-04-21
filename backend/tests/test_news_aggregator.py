"""
Unit tests for NewsAggregator class.
"""
import pytest
from datetime import datetime, timezone
from app.services.news.aggregator import NewsAggregator
from app.schemas.news import NewsArticle, NewsCategory, SentimentLabel


class TestNewsAggregator:
    """Test suite for NewsAggregator"""
    
    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance"""
        return NewsAggregator()
    
    def test_aggregator_initialization(self, aggregator):
        """Test that aggregator initializes with all sources"""
        assert len(aggregator.sources) == 6
        assert 'newsapi' in aggregator.sources
        assert 'gnews' in aggregator.sources
        assert 'finnhub' in aggregator.sources
        assert 'alpha_vantage' in aggregator.sources
        assert 'marketaux' in aggregator.sources
        assert 'fmp' in aggregator.sources
    
    def test_calculate_similarity_identical(self, aggregator):
        """Test similarity calculation for identical strings"""
        text1 = "Reliance Industries reports strong Q4 earnings"
        text2 = "Reliance Industries reports strong Q4 earnings"
        similarity = aggregator._calculate_similarity(text1, text2)
        assert similarity == 1.0
    
    def test_calculate_similarity_different(self, aggregator):
        """Test similarity calculation for different strings"""
        text1 = "Reliance Industries reports strong Q4 earnings"
        text2 = "TCS announces new AI partnership"
        similarity = aggregator._calculate_similarity(text1, text2)
        assert similarity < 0.3
    
    def test_calculate_similarity_similar(self, aggregator):
        """Test similarity calculation for similar strings"""
        text1 = "Reliance Industries reports strong Q4 earnings"
        text2 = "Reliance Industries reports Q4 earnings strong"
        similarity = aggregator._calculate_similarity(text1, text2)
        assert similarity > 0.8
    
    def test_calculate_similarity_empty(self, aggregator):
        """Test similarity calculation with empty strings"""
        similarity = aggregator._calculate_similarity("", "test")
        assert similarity == 0.0
        
        similarity = aggregator._calculate_similarity("test", "")
        assert similarity == 0.0
    
    def test_deduplicate_articles_by_url(self, aggregator):
        """Test deduplication removes articles with same URL"""
        articles = [
            NewsArticle(
                id="1",
                title="Article 1",
                description="Description 1",
                url="https://example.com/article1",
                source="Source1",
                published_at=datetime.now(timezone.utc),
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0
            ),
            NewsArticle(
                id="2",
                title="Article 1 Duplicate",
                description="Description 2",
                url="https://example.com/article1",  # Same URL
                source="Source2",
                published_at=datetime.now(timezone.utc),
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0
            ),
            NewsArticle(
                id="3",
                title="Article 2",
                description="Description 3",
                url="https://example.com/article2",
                source="Source3",
                published_at=datetime.now(timezone.utc),
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0
            )
        ]
        
        unique = aggregator.deduplicate_articles(articles)
        assert len(unique) == 2
        assert unique[0].url == "https://example.com/article1"
        assert unique[1].url == "https://example.com/article2"
    
    def test_deduplicate_articles_by_title_similarity(self, aggregator):
        """Test deduplication removes articles with similar titles"""
        articles = [
            NewsArticle(
                id="1",
                title="Reliance Industries reports strong Q4 earnings",
                description="Description 1",
                url="https://example.com/article1",
                source="Source1",
                published_at=datetime.now(timezone.utc),
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0
            ),
            NewsArticle(
                id="2",
                title="Reliance Industries reports strong Q4 earnings results",
                description="Description 2",
                url="https://example.com/article2",
                source="Source2",
                published_at=datetime.now(timezone.utc),
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0
            ),
            NewsArticle(
                id="3",
                title="TCS announces new AI partnership",
                description="Description 3",
                url="https://example.com/article3",
                source="Source3",
                published_at=datetime.now(timezone.utc),
                category=NewsCategory.GENERAL,
                sentiment=SentimentLabel.NEUTRAL,
                sentiment_score=0.0,
                sentiment_confidence=0.0
            )
        ]
        
        unique = aggregator.deduplicate_articles(articles)
        # Should keep first article and the TCS article (different topic)
        assert len(unique) == 2
        assert "Reliance" in unique[0].title
        assert "TCS" in unique[1].title
    
    def test_classify_category(self, aggregator):
        """Test category classification"""
        assert aggregator._classify_category("earnings") == NewsCategory.EARNINGS
        assert aggregator._classify_category("EARNINGS") == NewsCategory.EARNINGS
        assert aggregator._classify_category("merger") == NewsCategory.MERGER
        assert aggregator._classify_category("regulatory") == NewsCategory.REGULATORY
        assert aggregator._classify_category("unknown") == NewsCategory.GENERAL
        assert aggregator._classify_category("") == NewsCategory.GENERAL
    
    def test_normalize_newsapi_article(self, aggregator):
        """Test NewsAPI article normalization"""
        raw = {
            "title": "Test Article",
            "description": "Test description",
            "url": "https://example.com/test",
            "source": {"name": "Test Source"},
            "publishedAt": "2024-01-15T10:30:00Z",
            "urlToImage": "https://example.com/image.jpg"
        }
        
        article = aggregator._normalize_newsapi_article(raw)
        assert article is not None
        assert article.title == "Test Article"
        assert article.description == "Test description"
        assert article.url == "https://example.com/test"
        assert article.source == "Test Source"
        assert article.image_url == "https://example.com/image.jpg"
        assert article.sentiment == SentimentLabel.NEUTRAL
        assert article.sentiment_score == 0.0
    
    def test_normalize_newsapi_article_missing_required_fields(self, aggregator):
        """Test NewsAPI normalization with missing required fields"""
        raw = {
            "title": "Test Article",
            # Missing url and publishedAt
        }
        
        article = aggregator._normalize_newsapi_article(raw)
        assert article is None
    
    def test_normalize_finnhub_article(self, aggregator):
        """Test Finnhub article normalization"""
        raw = {
            "id": 12345,
            "headline": "Test Headline",
            "summary": "Test summary",
            "url": "https://example.com/test",
            "source": "Test Source",
            "datetime": 1705318200,  # Unix timestamp
            "image": "https://example.com/image.jpg",
            "category": "earnings"
        }
        
        article = aggregator._normalize_finnhub_article(raw, "RELIANCE")
        assert article is not None
        assert article.title == "Test Headline"
        assert article.description == "Test summary"
        assert article.ticker == "RELIANCE"
        assert article.category == NewsCategory.EARNINGS
        assert "RELIANCE" in article.related_tickers

    def test_normalize_fmp_article(self, aggregator):
        """Test FMP article normalization"""
        raw = {
            "title": "FMP Test Article",
            "text": "FMP test description",
            "url": "https://example.com/fmp-test",
            "site": "Financial Modeling Prep",
            "publishedDate": "2024-03-21 12:00:00",
            "image": "https://example.com/fmp-image.jpg"
        }
        
        article = aggregator._normalize_fmp_article(raw, "AAPL")
        assert article is not None
        assert article.title == "FMP Test Article"
        assert article.description == "FMP test description"
        assert article.ticker == "AAPL"
        assert article.source == "Financial Modeling Prep"
        assert article.published_at is not None
        assert article.published_at.year == 2024
    
    @pytest.mark.asyncio
    async def test_aggregate_all_sources_with_no_api_keys(self, aggregator):
        """Test aggregation when no API keys are configured"""
        # This should not raise an error, just return empty results
        articles = await aggregator.aggregate_all_sources("RELIANCE", limit=10)
        assert isinstance(articles, list)
        # Will be empty since no API keys are configured in test environment
