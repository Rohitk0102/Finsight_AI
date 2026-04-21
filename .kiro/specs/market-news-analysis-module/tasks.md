# Implementation Plan: Market News Analysis Module

## Overview

This implementation plan breaks down the Market News Analysis Module into discrete, testable coding tasks. The module extends the existing Finsight AI platform with real-time financial news aggregation, NLP-based sentiment analysis, and ML-based stock impact prediction for Indian large-cap companies (Nifty 50).

**Technology Stack:**
- Backend: Python (FastAPI, Pydantic, httpx, APScheduler)
- Frontend: TypeScript (Next.js 14, React 18)
- Cache: Redis
- External APIs: NewsAPI, GNews, Finnhub, Alpha Vantage, Marketaux, HuggingFace Inference API

**Implementation Order:**
1. Backend: News ingestion service + normalization + Redis caching
2. Backend: HuggingFace sentiment pipeline integration
3. Backend: Impact prediction endpoint
4. Backend: All API routes with filtering logic
5. Frontend: Filter bar component
6. Frontend: News card grid with skeleton loaders
7. Frontend: Detail modal/drawer
8. Frontend: Auto-refresh + optimistic UI updates
9. End-to-end integration test with real Nifty 50 tickers

## Tasks

- [x] 1. Set up backend data models and configuration
  - Create Pydantic schemas in `backend/app/schemas/news.py` for NewsArticle, ImpactPrediction, SentimentLabel, NewsCategory enums
  - Add environment variables to `backend/app/core/config.py`: NEWS_API_KEY, GNEWS_API_KEY, FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY, MARKETAUX_API_KEY, HUGGINGFACE_API_KEY
  - Create Nifty 50 company data file at `backend/app/data/nifty50.json` with all 50 companies, sectors, and exchange info
  - _Requirements: 1.3, 11.1, 11.2, 14.1_

- [ ] 2. Implement news aggregation service with multi-source fetching
  - [-] 2.1 Create NewsAggregator class in `backend/app/services/news/aggregator.py`
    - Implement `aggregate_all_sources()` method to orchestrate parallel fetching
    - Implement `_fetch_newsapi()` with India filter and error handling
    - Implement `_fetch_gnews()` with proper API parameter mapping
    - Implement `_fetch_finnhub()` with ticker-based queries
    - Implement `_fetch_alpha_vantage()` with news sentiment endpoint
    - Implement `_fetch_marketaux()` with India market filter
    - _Requirements: 1.1, 1.2, 1.4_
  
  - [ ] 2.2 Implement article normalization functions
    - Create `_normalize_newsapi_article()` to convert NewsAPI response to unified schema
    - Create normalization functions for each API source (GNews, Finnhub, Alpha Vantage, Marketaux)
    - Ensure all required fields (id, title, url, source, published_at) are populated
    - _Requirements: 1.3, 1.6_
  
  - [ ] 2.3 Implement article deduplication logic
    - Create `deduplicate_articles()` method to remove duplicates by URL
    - Implement `_calculate_similarity()` using Jaccard similarity for title comparison
    - Remove articles with title similarity > 0.9
    - _Requirements: 1.5_
  
  - [ ]*  2.4 Write property test for query construction with India filter
    - **Property 1: Query Construction with India Filter**
    - **Validates: Requirements 1.2**
    - Test that any company name/ticker generates query containing "India" or NSE suffix
  
  - [ ]* 2.5 Write property test for article normalization completeness
    - **Property 2: Article Normalization Completeness**
    - **Validates: Requirements 1.3**
    - Test that any valid external API response normalizes to complete schema with all required fields
  
  - [ ]* 2.6 Write property test for article deduplication
    - **Property 3: Article Deduplication Correctness**
    - **Validates: Requirements 1.5**
    - Test that duplicate articles (same URL or similar titles) are removed correctly

- [ ] 3. Implement Redis cache manager
  - [ ] 3.1 Create CacheManager class in `backend/app/services/news/cache.py`
    - Implement `get_cached_news()` to retrieve articles from Redis
    - Implement `set_cached_news()` with 15-minute TTL
    - Implement `invalidate_cache()` for ticker/sector-specific invalidation
    - Implement `generate_cache_key()` for consistent key generation from filters
    - _Requirements: 2.1, 2.2, 2.3, 2.5_
  
  - [ ]* 3.2 Write property test for cache key generation consistency
    - **Property 4: Cache Key Generation Consistency**
    - **Validates: Requirements 2.3**
    - Test that same filter parameters always produce identical cache keys

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement sentiment analysis service
  - [ ] 5.1 Create SentimentAnalyzer class in `backend/app/services/news/sentiment.py`
    - Initialize with HuggingFace API credentials and model list (ProsusAI/finbert, yiyanghkust/finbert-tone, mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis)
    - Implement `analyze_sentiment()` method with text truncation to 512 tokens
    - Implement `_ensemble_predict()` to call all 3 BERT models in parallel
    - Implement `_combine_predictions()` using voting mechanism
    - Implement `_normalize_label()` to standardize sentiment labels
    - Implement `_convert_score()` to map confidence to -1 to 1 scale
    - Implement `_fallback_sentiment()` returning neutral sentiment
    - Track character usage to stay within 30,000 character monthly limit
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [ ]* 5.2 Write property test for text truncation to token limit
    - **Property 5: Text Truncation to Token Limit**
    - **Validates: Requirements 4.2**
    - Test that any article text is truncated to max 512 tokens
  
  - [ ]* 5.3 Write property test for sentiment output structure validation
    - **Property 6: Sentiment Output Structure Validation**
    - **Validates: Requirements 4.3**
    - Test that sentiment results contain valid label and confidence in [0.0, 1.0]
  
  - [ ]* 5.4 Write property test for character usage tracking accuracy
    - **Property 7: Character Usage Tracking Accuracy**
    - **Validates: Requirements 4.6**
    - Test that tracked character count equals sum of all processed text lengths
  
  - [ ]* 5.5 Write property test for sentiment serialization round-trip
    - **Property 8: Sentiment Serialization Round-Trip**
    - **Validates: Requirements 4.7**
    - Test that sentiment object serialization and deserialization preserves values

- [ ] 6. Implement stock impact prediction service
  - [ ] 6.1 Create ImpactPredictor class in `backend/app/services/news/impact.py`
    - Implement `predict_impact()` accepting sentiment_label, sentiment_score, ticker, sector, news_type
    - Implement `apply_sector_weighting()` to adjust predictions based on sector factors
    - Implement `classify_magnitude()` to determine high/medium/low impact
    - Return predicted_impact (bullish/bearish/neutral), confidence, magnitude, reasoning
    - Classify as neutral when confidence < 0.5
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [ ]* 6.2 Write property test for impact prediction input acceptance
    - **Property 9: Impact Prediction Input Acceptance**
    - **Validates: Requirements 5.2**
    - Test that valid input combinations are accepted without validation errors
  
  - [ ]* 6.3 Write property test for impact prediction output structure
    - **Property 10: Impact Prediction Output Structure**
    - **Validates: Requirements 5.3**
    - Test that output contains predicted_impact, confidence [0.0, 1.0], and magnitude
  
  - [ ]* 6.4 Write property test for low confidence classification
    - **Property 11: Low Confidence Classification**
    - **Validates: Requirements 5.4**
    - Test that predictions with confidence < 0.5 are classified as neutral
  
  - [ ]* 6.5 Write property test for sector weighting application
    - **Property 12: Sector Weighting Application**
    - **Validates: Requirements 5.5**
    - Test that sector-specific weighting factors are applied to confidence scores

- [ ] 7. Implement rate limit manager
  - Create RateLimiter class in `backend/app/services/news/rate_limiter.py`
  - Implement `check_rate_limit()` to verify if API call is allowed
  - Implement `increment_counter()` to track API call counts per source
  - Implement `reset_counters()` for hourly counter reset
  - Implement `prioritize_sources()` to select sources when rate limited
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement news API endpoints
  - [ ] 9.1 Create news router in `backend/app/api/routes/news.py`
    - Implement POST `/api/v1/news/fetch` endpoint to trigger manual news fetch
    - Implement GET `/api/v1/news` endpoint with pagination and filtering (ticker, sector, newsType, timeRange, sentiment)
    - Implement GET `/api/v1/news/:id` endpoint for single article retrieval
    - Implement POST `/api/v1/news/analyze` endpoint for custom article analysis
    - Implement GET `/api/v1/tickers/nifty50` endpoint returning Nifty 50 company list
    - Implement GET `/api/v1/news/trending` endpoint for top 5 most-impactful stories
    - Add request validation using Pydantic schemas
    - Add error handling with structured error responses
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_
  
  - [ ] 9.2 Integrate cache layer with API endpoints
    - Check cache before fetching from external APIs
    - Store fetched articles in cache with 15-minute TTL
    - Return cached data within 200ms for cache hits
    - _Requirements: 2.1, 2.2, 15.1_
  
  - [ ] 9.3 Wire sentiment and impact services into news fetching flow
    - Call SentimentAnalyzer after article normalization
    - Call ImpactPredictor after sentiment analysis
    - Handle service failures gracefully with fallback values
    - _Requirements: 4.1, 5.1, 13.1, 13.2, 13.3_
  
  - [ ]* 9.4 Write property test for trending articles selection
    - **Property 13: Trending Articles Selection**
    - **Validates: Requirements 6.6**
    - Test that trending endpoint returns top 5 articles by impact score in descending order
  
  - [ ]* 9.5 Write property test for error response structure consistency
    - **Property 14: Error Response Structure Consistency**
    - **Validates: Requirements 16.3, 17.3**
    - Test that all error responses contain error_code, message, and timestamp
  
  - [ ]* 9.6 Write property test for request parameter validation
    - **Property 15: Request Parameter Validation**
    - **Validates: Requirements 17.1**
    - Test that Pydantic validation rejects invalid parameters before processing
  
  - [ ]* 9.7 Write property test for article schema validation before caching
    - **Property 16: Article Schema Validation Before Caching**
    - **Validates: Requirements 17.2**
    - Test that articles are validated before storing in cache
  
  - [ ]* 9.8 Write property test for ticker validation against Nifty 50
    - **Property 17: Ticker Validation Against Nifty 50**
    - **Validates: Requirements 17.5**
    - Test that ticker validation returns true only for Nifty 50 members
  
  - [ ]* 9.9 Write property test for pagination page size limit
    - **Property 22: Pagination Page Size Limit**
    - **Validates: Requirements 15.2**
    - Test that returned pages contain at most 50 articles regardless of requested limit

- [ ] 10. Register news router in main application
  - Add news router to `backend/app/main.py` with API prefix
  - Ensure CORS middleware allows frontend origin
  - _Requirements: 6.1_

- [ ] 11. Implement background news refresh scheduler
  - Create news refresh job in `backend/app/tasks/news_refresh.py`
  - Use APScheduler to schedule job every 15 minutes
  - Implement `refresh_nifty50_news()` to fetch news for all Nifty 50 companies
  - Implement retry logic for failed jobs (max 3 retries, 5-minute delay)
  - Track last successful refresh timestamp
  - Update cache with newly fetched articles
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Create frontend TypeScript types and API client
  - [ ] 13.1 Create TypeScript types in `frontend/types/news.ts`
    - Define NewsArticle interface matching backend schema
    - Define ImpactPrediction, SentimentLabel, NewsCategory types
    - Define NewsFilters interface for filter state
    - Define Nifty50Company interface
  
  - [ ] 13.2 Create news API client in `frontend/lib/api/news.ts`
    - Implement `fetchNews()` with pagination and filtering
    - Implement `fetchArticleById()` for single article retrieval
    - Implement `fetchNifty50Companies()` for company list
    - Implement `fetchTrendingNews()` for trending articles
    - Implement `triggerNewsFetch()` for manual refresh
    - Add error handling and toast notifications
    - _Requirements: 6.2, 6.3, 6.5, 6.6_

- [ ] 14. Implement filter bar component
  - [ ] 14.1 Create FilterBar component in `frontend/components/news/FilterBar.tsx`
    - Add search input with ticker autocomplete using datalist
    - Add multi-select dropdown for sector filtering
    - Add chip-based selector for news type (earnings, merger, regulatory, market_analysis, general)
    - Add toggle buttons for time range (1h, 6h, 24h, 7d, 30d)
    - Add sentiment filter dropdown (positive, negative, neutral, all)
    - Implement debounced search (300ms delay)
    - Display active filter count badge
    - Add clear filters button
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_
  
  - [ ] 14.2 Implement URL query parameter sync
    - Store active filters in URL query parameters
    - Restore filters from URL on page load
    - Update URL when filters change without page reload
    - _Requirements: 18.1, 18.2, 18.3_

- [ ] 15. Implement news card component
  - Create NewsCard component in `frontend/components/news/NewsCard.tsx`
  - Display article thumbnail (80x56px) with Next.js Image component
  - Display source badge, category badge, and sentiment badge with icon
  - Display article title (max 2 lines with ellipsis)
  - Display article description (max 2 lines with ellipsis)
  - Display ticker chips for related stocks
  - Display impact prediction badge with color coding (bullish=green, bearish=red, neutral=amber)
  - Display source name and relative timestamp using date-fns
  - Add colored left border matching sentiment (green=positive, red=negative, amber=neutral)
  - Show external link icon on hover
  - Open article URL in new tab on click
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10_

- [ ] 16. Implement news feed page with grid layout
  - [ ] 16.1 Create news feed page in `frontend/app/news/page.tsx`
    - Implement responsive grid layout (3 columns desktop, 2 tablet, 1 mobile)
    - Add page header with title and article count badge
    - Integrate FilterBar component
    - Render NewsCard components in grid
    - Implement skeleton loaders for 5 cards during loading
    - Implement empty state with icon and message when no articles found
    - Add staggered card entrance animations (40ms delay per card, max 400ms)
    - _Requirements: 7.1, 7.3, 7.4, 7.5, 7.6_
  
  - [ ] 16.2 Implement auto-refresh functionality
    - Create useAutoRefresh hook to refresh news every 15 minutes
    - Display toast notification when new articles are available
    - Maintain scroll position during refresh
    - _Requirements: 7.2, 18.4_

- [ ] 17. Implement article detail modal
  - Create ArticleDetailModal component in `frontend/components/news/ArticleDetailModal.tsx`
  - Display full article title and description
  - Display sentiment gauge chart using Recharts showing confidence score
  - Display stock price sparkline for related ticker (last 7 days) using Recharts
  - Display impact prediction with confidence percentage
  - Display list of related articles (same ticker, last 24 hours)
  - Add "Read Full Article" button linking to source
  - Implement keyboard navigation (Escape to close)
  - Implement focus trap for accessibility
  - Close modal when clicking outside
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

- [ ] 18. Implement accessibility features
  - Add keyboard navigation support to FilterBar (Tab, Enter, Escape)
  - Make NewsCard focusable and activatable via keyboard
  - Add ARIA labels to all interactive elements
  - Ensure color contrast ratio of at least 4.5:1 for text
  - Test with screen reader
  - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

- [ ] 19. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Write integration tests for external API sources
  - [ ]* 20.1 Write integration test for NewsAPI with 3 examples
    - Test queries for RELIANCE, TCS, INFY
    - Verify minimum 1 result per query
    - Verify source field is "NewsAPI"
    - _Requirements: 20.1_
  
  - [ ]* 20.2 Write integration tests for other API sources
    - Test GNews, Finnhub, Alpha Vantage, Marketaux with representative examples
    - Verify normalization produces valid NewsArticle objects
    - _Requirements: 20.1_

- [ ]* 21. Write unit tests for backend services
  - Write unit tests for sentiment analysis fallback logic
  - Write unit tests for impact prediction classification
  - Write unit tests for error handling and logging
  - Write unit tests for rate limit tracking
  - Write unit tests for cache key generation
  - _Requirements: 20.2, 20.3, 20.4_

- [ ]* 22. Write frontend component tests
  - Write tests for FilterBar interactions (search, multi-select, chips, toggles)
  - Write tests for NewsCard rendering with various data states
  - Write tests for ArticleDetailModal (open, close, keyboard navigation)
  - Write tests for loading states and skeleton loaders
  - Write tests for empty states
  - Write tests for error states and toast notifications
  - _Requirements: 20.5_

- [ ] 23. End-to-end integration test with real Nifty 50 tickers
  - Test complete flow: fetch news → normalize → analyze sentiment → predict impact → cache → display
  - Test with at least 5 Nifty 50 tickers (RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK)
  - Verify all components work together correctly
  - Verify cache hit/miss behavior
  - Verify auto-refresh updates UI
  - _Requirements: All requirements_

- [ ] 24. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (23 properties total)
- Unit tests validate specific examples and edge cases
- Integration tests verify external API integrations
- The implementation follows the order specified: backend services → API routes → frontend components → integration
- All backend code uses Python with FastAPI, Pydantic, httpx, APScheduler
- All frontend code uses TypeScript with Next.js 14, React 18
- Redis is used for caching with 15-minute TTL
- HuggingFace Inference API is used for sentiment analysis and impact prediction
