# Requirements Document

## Introduction

The Market News Analysis Module is a production-grade feature for an existing full-stack application (Next.js frontend + FastAPI backend) that provides real-time financial news ingestion, NLP-based sentiment analysis, and ML-based stock impact prediction focused on Indian large-cap companies (Nifty 50 / BSE Sensex constituents). The system aggregates news from multiple free-tier sources, analyzes sentiment using pretrained BERT models via HuggingFace Inference API, predicts stock impact, and presents results through a responsive, Netflix-style news feed interface with advanced filtering capabilities.

## Glossary

- **News_Aggregator**: Backend service that fetches and normalizes financial news from multiple external APIs
- **Sentiment_Analyzer**: NLP pipeline that analyzes article sentiment using HuggingFace BERT models
- **Impact_Predictor**: ML service that predicts stock price impact based on news sentiment and metadata
- **News_API**: Backend FastAPI service exposing news endpoints
- **News_Feed_UI**: Frontend Next.js component displaying news cards with filters
- **Cache_Manager**: Redis-based caching layer for news data
- **Background_Scheduler**: APScheduler service for periodic news refresh
- **Article**: Normalized news data structure with sentiment and impact predictions
- **Nifty_50**: Index of 50 large-cap Indian companies traded on NSE
- **HuggingFace_Inference_API**: Free-tier API for running pretrained NLP models
- **Filter_Bar**: UI component for filtering news by ticker, sector, sentiment, time range
- **News_Card**: UI component displaying individual article with metadata
- **Detail_Modal**: UI component showing full article analysis with charts

## Requirements

### Requirement 1: News Ingestion from Multiple Sources

**User Story:** As a backend service, I want to fetch financial news from multiple free-tier APIs, so that I can provide comprehensive market coverage for Indian large-cap companies.

#### Acceptance Criteria

1. THE News_Aggregator SHALL fetch news from NewsAPI, GNews, Finnhub, Alpha Vantage, and Marketaux APIs
2. WHEN fetching news for Indian companies, THE News_Aggregator SHALL append "India" or NSE ticker to search queries
3. THE News_Aggregator SHALL normalize articles into unified schema with fields: id, title, description, url, source, publishedAt, imageUrl, relatedTickers, category, sentimentScore, impactPrediction
4. WHEN an external API request fails, THE News_Aggregator SHALL log the error and continue with remaining sources
5. THE News_Aggregator SHALL deduplicate articles based on URL and title similarity
6. FOR ALL fetched articles, THE News_Aggregator SHALL validate required fields (title, url, source, publishedAt) are present

### Requirement 2: News Data Caching

**User Story:** As a backend service, I want to cache news data in Redis, so that I can reduce external API calls and stay within free-tier rate limits.

#### Acceptance Criteria

1. THE Cache_Manager SHALL store fetched articles in Redis with TTL of 15 minutes
2. WHEN a news request is received, THE Cache_Manager SHALL check Redis cache before calling external APIs
3. THE Cache_Manager SHALL use cache keys based on filter parameters (ticker, sector, timeRange, sentiment)
4. WHEN cache TTL expires, THE Cache_Manager SHALL mark cached data as stale
5. THE Cache_Manager SHALL support cache invalidation for specific tickers or sectors

### Requirement 3: Background News Refresh

**User Story:** As a backend service, I want to automatically refresh news data every 15 minutes, so that users see up-to-date market information without manual intervention.

#### Acceptance Criteria

1. THE Background_Scheduler SHALL execute news fetch job every 15 minutes
2. WHEN the scheduled job runs, THE Background_Scheduler SHALL fetch news for all Nifty 50 companies
3. IF a scheduled job fails, THEN THE Background_Scheduler SHALL log the error and retry after 5 minutes
4. THE Background_Scheduler SHALL update cache with newly fetched articles
5. THE Background_Scheduler SHALL track last successful refresh timestamp

### Requirement 4: Sentiment Analysis Pipeline

**User Story:** As a backend service, I want to analyze article sentiment using pretrained BERT models, so that I can provide AI-powered sentiment scores for each news article.

#### Acceptance Criteria

1. THE Sentiment_Analyzer SHALL use HuggingFace Inference API with models: ProsusAI/finbert, yiyanghkust/finbert-tone, mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis
2. WHEN analyzing an article, THE Sentiment_Analyzer SHALL process title and first 512 tokens of description
3. THE Sentiment_Analyzer SHALL return sentiment label (positive, negative, neutral) and confidence score (0.0 to 1.0)
4. WHEN HuggingFace API is unavailable, THE Sentiment_Analyzer SHALL return neutral sentiment with score 0.0
5. THE Sentiment_Analyzer SHALL batch process multiple articles to optimize API usage
6. THE Sentiment_Analyzer SHALL track monthly character usage to stay within 30,000 character free-tier limit
7. FOR ALL analyzed articles, parsing the sentiment result then formatting then parsing SHALL produce an equivalent sentiment object (round-trip property)

### Requirement 5: Stock Impact Prediction

**User Story:** As a backend service, I want to predict stock price impact from news sentiment, so that users can understand potential market effects of news events.

#### Acceptance Criteria

1. THE Impact_Predictor SHALL use HuggingFace model: nickmuchi/finbert-tone-financial-news-sentiment-analysis
2. WHEN predicting impact, THE Impact_Predictor SHALL accept input: sentiment_label, sentiment_score, ticker, sector, news_type
3. THE Impact_Predictor SHALL return: predicted_impact (bullish, bearish, neutral), confidence (0.0 to 1.0), magnitude (high, medium, low)
4. WHEN confidence score is below 0.5, THE Impact_Predictor SHALL classify impact as neutral
5. THE Impact_Predictor SHALL apply sector-specific weighting to impact predictions
6. FOR ALL valid prediction inputs, THE Impact_Predictor SHALL return a prediction within 5 seconds

### Requirement 6: News API Endpoints

**User Story:** As a frontend application, I want to access news data through RESTful API endpoints, so that I can display filtered and paginated news to users.

#### Acceptance Criteria

1. THE News_API SHALL expose POST /api/v1/news/fetch endpoint to trigger news fetch and cache update
2. THE News_API SHALL expose GET /api/v1/news endpoint with pagination (page, limit) and filters (ticker, sector, newsType, timeRange, sentiment)
3. THE News_API SHALL expose GET /api/v1/news/:id endpoint to retrieve single article with full analysis
4. THE News_API SHALL expose POST /api/v1/news/analyze endpoint to run sentiment and impact analysis on a single article
5. THE News_API SHALL expose GET /api/v1/tickers/nifty50 endpoint returning static list of Nifty 50 companies with sectors
6. THE News_API SHALL expose GET /api/v1/news/trending endpoint returning top 5 most-impactful stories from last 24 hours
7. WHEN invalid filter parameters are provided, THE News_API SHALL return 400 error with descriptive message
8. THE News_API SHALL return responses within 2 seconds for cached data

### Requirement 7: News Feed User Interface

**User Story:** As a user, I want to view financial news in a responsive card-based layout, so that I can quickly scan market news on any device.

#### Acceptance Criteria

1. THE News_Feed_UI SHALL display articles in a responsive grid (3 columns desktop, 2 tablet, 1 mobile)
2. THE News_Feed_UI SHALL auto-refresh news data every 15 minutes
3. WHEN loading news, THE News_Feed_UI SHALL display skeleton loaders for 5 cards
4. WHEN no articles match filters, THE News_Feed_UI SHALL display empty state with icon and message
5. THE News_Feed_UI SHALL animate card entrance with staggered delays (40ms per card, max 400ms)
6. THE News_Feed_UI SHALL display article count badge in header

### Requirement 8: Filter Bar Component

**User Story:** As a user, I want to filter news by multiple criteria, so that I can focus on relevant market information.

#### Acceptance Criteria

1. THE Filter_Bar SHALL provide search input for ticker filtering with autocomplete
2. THE Filter_Bar SHALL provide multi-select dropdown for sector filtering
3. THE Filter_Bar SHALL provide chip-based selector for news type (earnings, merger, regulatory, market_analysis, general)
4. THE Filter_Bar SHALL provide toggle buttons for time range (1h, 6h, 24h, 7d, 30d)
5. THE Filter_Bar SHALL provide sentiment filter (positive, negative, neutral, all)
6. WHEN Enter key is pressed in search input, THE Filter_Bar SHALL apply filters
7. WHEN Clear button is clicked, THE Filter_Bar SHALL reset all filters to default values
8. THE Filter_Bar SHALL display active filter count badge

### Requirement 9: News Card Component

**User Story:** As a user, I want to see key article information in a compact card format, so that I can quickly assess news relevance and sentiment.

#### Acceptance Criteria

1. THE News_Card SHALL display article thumbnail (80x56px) on desktop and tablet
2. THE News_Card SHALL display source badge, category badge, and sentiment badge with icon
3. THE News_Card SHALL display article title (max 2 lines with ellipsis)
4. THE News_Card SHALL display article description (max 2 lines with ellipsis)
5. THE News_Card SHALL display ticker chips for related stocks
6. THE News_Card SHALL display impact prediction badge (bullish/bearish/neutral with color coding)
7. THE News_Card SHALL display source name and relative timestamp (e.g., "2 hours ago")
8. THE News_Card SHALL show external link icon on hover
9. THE News_Card SHALL have colored left border matching sentiment (green=positive, red=negative, amber=neutral)
10. WHEN clicked, THE News_Card SHALL open article URL in new tab

### Requirement 10: Article Detail Modal

**User Story:** As a user, I want to view detailed article analysis in a modal, so that I can see full sentiment breakdown and related market data.

#### Acceptance Criteria

1. THE Detail_Modal SHALL display full article title and description
2. THE Detail_Modal SHALL display sentiment gauge chart showing confidence score
3. THE Detail_Modal SHALL display stock price sparkline for related ticker (last 7 days)
4. THE Detail_Modal SHALL display impact prediction with confidence percentage
5. THE Detail_Modal SHALL display list of related articles (same ticker, last 24 hours)
6. WHEN Escape key is pressed, THE Detail_Modal SHALL close
7. WHEN clicking outside modal, THE Detail_Modal SHALL close
8. THE Detail_Modal SHALL display "Read Full Article" button linking to source

### Requirement 11: Nifty 50 Company Data

**User Story:** As a backend service, I want to maintain a static list of Nifty 50 companies with sectors, so that I can provide accurate ticker autocomplete and sector filtering.

#### Acceptance Criteria

1. THE News_API SHALL store Nifty 50 company data with fields: ticker, name, sector, exchange (NSE)
2. THE News_API SHALL include all 11 sectors: Financial Services, IT, Oil & Gas, FMCG, Automobile, Pharma, Metals, Telecom, Power, Cement, Consumer Durables
3. THE News_API SHALL update company list when Nifty 50 constituents change
4. THE News_API SHALL return company data sorted alphabetically by ticker

### Requirement 12: Rate Limit Management

**User Story:** As a backend service, I want to manage external API rate limits, so that I stay within free-tier quotas and avoid service disruptions.

#### Acceptance Criteria

1. THE News_Aggregator SHALL track API call count per source per hour
2. WHEN approaching rate limit (90% of quota), THE News_Aggregator SHALL reduce fetch frequency
3. WHEN rate limit is exceeded, THE News_Aggregator SHALL skip that source and log warning
4. THE News_Aggregator SHALL reset rate limit counters hourly
5. THE News_Aggregator SHALL prioritize high-impact news sources when rate limited

### Requirement 13: Graceful Degradation

**User Story:** As a user, I want to see news articles even when sentiment analysis is unavailable, so that I can still access market information during service disruptions.

#### Acceptance Criteria

1. WHEN HuggingFace API is unavailable, THE News_Feed_UI SHALL display articles without sentiment badges
2. WHEN sentiment analysis fails, THE News_Feed_UI SHALL show "Analysis Pending" badge
3. WHEN impact prediction fails, THE News_Feed_UI SHALL hide impact prediction badge
4. THE News_Feed_UI SHALL display error toast notification when analysis services are degraded
5. THE News_Feed_UI SHALL retry failed sentiment analysis after 5 minutes

### Requirement 14: API Configuration Management

**User Story:** As a developer, I want to configure external API keys through environment variables, so that I can manage credentials securely across environments.

#### Acceptance Criteria

1. THE News_Aggregator SHALL read API keys from environment variables: NEWS_API_KEY, GNEWS_API_KEY, FINNHUB_API_KEY, HUGGINGFACE_API_KEY
2. WHEN a required API key is missing, THE News_Aggregator SHALL log warning and skip that source
3. THE News_Aggregator SHALL validate API key format on startup
4. THE News_Aggregator SHALL support API key rotation without service restart

### Requirement 15: Performance Optimization

**User Story:** As a user, I want news data to load quickly, so that I can access market information without delays.

#### Acceptance Criteria

1. THE News_API SHALL return cached news data within 200 milliseconds
2. THE News_API SHALL return paginated results with maximum 50 articles per page
3. THE News_Feed_UI SHALL implement virtual scrolling for lists exceeding 100 articles
4. THE News_Feed_UI SHALL lazy-load article thumbnails using Next.js Image component
5. THE News_Feed_UI SHALL debounce filter input changes by 300 milliseconds

### Requirement 16: Error Handling and Logging

**User Story:** As a developer, I want comprehensive error logging, so that I can diagnose and fix issues quickly.

#### Acceptance Criteria

1. THE News_Aggregator SHALL log all external API errors with source, endpoint, and error message
2. THE Sentiment_Analyzer SHALL log failed analysis attempts with article ID and error details
3. THE News_API SHALL return structured error responses with error code, message, and timestamp
4. WHEN an unhandled exception occurs, THE News_API SHALL return 500 error and log full stack trace
5. THE Background_Scheduler SHALL log job execution time and success/failure status

### Requirement 17: Data Validation

**User Story:** As a backend service, I want to validate all incoming and outgoing data, so that I maintain data integrity and prevent errors.

#### Acceptance Criteria

1. THE News_API SHALL validate request parameters using Pydantic schemas
2. THE News_Aggregator SHALL validate article schema before storing in cache
3. WHEN invalid data is detected, THE News_API SHALL return 422 error with field-level validation messages
4. THE Sentiment_Analyzer SHALL validate sentiment score is between 0.0 and 1.0
5. THE Impact_Predictor SHALL validate ticker exists in Nifty 50 list before prediction

### Requirement 18: Frontend State Management

**User Story:** As a user, I want filter selections to persist during my session, so that I don't lose my preferences when navigating away.

#### Acceptance Criteria

1. THE News_Feed_UI SHALL store active filters in URL query parameters
2. WHEN page is refreshed, THE News_Feed_UI SHALL restore filters from URL
3. THE News_Feed_UI SHALL update URL when filters change without page reload
4. THE News_Feed_UI SHALL maintain scroll position when applying filters
5. THE News_Feed_UI SHALL clear filters when navigating to news page without query parameters

### Requirement 19: Accessibility Compliance

**User Story:** As a user with accessibility needs, I want the news interface to be keyboard navigable and screen-reader friendly, so that I can access market information independently.

#### Acceptance Criteria

1. THE Filter_Bar SHALL support keyboard navigation (Tab, Enter, Escape)
2. THE News_Card SHALL be focusable and activatable via keyboard
3. THE Detail_Modal SHALL trap focus and support Escape key to close
4. THE News_Feed_UI SHALL provide ARIA labels for all interactive elements
5. THE News_Feed_UI SHALL maintain color contrast ratio of at least 4.5:1 for text

### Requirement 20: Testing Requirements

**User Story:** As a developer, I want comprehensive test coverage, so that I can ensure system reliability and catch regressions early.

#### Acceptance Criteria

1. THE News_Aggregator SHALL have integration tests for each external API source with 3 representative examples
2. THE Sentiment_Analyzer SHALL have unit tests verifying sentiment label and score ranges
3. THE News_API SHALL have endpoint tests covering success cases, validation errors, and error handling
4. THE Cache_Manager SHALL have unit tests for cache hit, miss, and expiration scenarios
5. THE News_Feed_UI SHALL have component tests for filter interactions and card rendering
6. FOR ALL News_Aggregator normalization functions, processing then serializing then processing SHALL produce equivalent article objects (round-trip property)

