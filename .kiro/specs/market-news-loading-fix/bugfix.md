# Bugfix Requirements Document

## Introduction

The market news page fails to load news articles, displaying "Failed to load news" error. The backend API endpoint `/api/v1/news/market` returns a 500 Internal Server Error due to a schema field mismatch between the Pydantic model definition and the service layer implementation. The `NewsArticle` schema expects a `description` field, but the `NewsService` creates articles with a `summary` field, causing validation to fail when the API attempts to serialize the response.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the `/api/v1/news/market` endpoint is called THEN the system returns a 500 Internal Server Error

1.2 WHEN the `NewsService.get_market_news()` method creates `NewsArticle` objects with `summary` field THEN Pydantic validation fails because the schema expects `description`

1.3 WHEN the `NewsService.get_stock_news()` method creates `NewsArticle` objects with `summary` field THEN Pydantic validation fails because the schema expects `description`

1.4 WHEN the frontend calls `newsApi.market(30)` THEN the page displays "Failed to load news" toast error

### Expected Behavior (Correct)

2.1 WHEN the `/api/v1/news/market` endpoint is called THEN the system SHALL return a 200 OK response with a list of news articles

2.2 WHEN the `NewsService.get_market_news()` method creates `NewsArticle` objects THEN it SHALL use the `description` field to match the schema definition

2.3 WHEN the `NewsService.get_stock_news()` method creates `NewsArticle` objects THEN it SHALL use the `description` field to match the schema definition

2.4 WHEN the frontend calls `newsApi.market(30)` THEN the page SHALL successfully load and display market news articles with sentiment analysis

### Unchanged Behavior (Regression Prevention)

3.1 WHEN news articles are fetched from Finnhub API THEN the system SHALL CONTINUE TO extract the summary/description content from the API response

3.2 WHEN news articles are fetched from NewsAPI THEN the system SHALL CONTINUE TO extract the description content from the API response

3.3 WHEN sentiment analysis is performed on news articles THEN the system SHALL CONTINUE TO calculate sentiment scores correctly

3.4 WHEN news articles are cached in Redis THEN the system SHALL CONTINUE TO cache them with the correct TTL

3.5 WHEN the frontend displays news articles THEN the system SHALL CONTINUE TO show the article summary/description text in the UI

3.6 WHEN news articles are sorted and deduplicated THEN the system SHALL CONTINUE TO sort by published_at descending and remove duplicates by title
