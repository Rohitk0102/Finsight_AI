# Market News Loading Fix - Bugfix Design

## Overview

The market news page fails to load due to a field name mismatch between the Pydantic schema and the service layer. The `NewsArticle` schema defines a `description` field, but the `NewsService` creates article objects using `summary` as the field name. This causes Pydantic validation to fail when the API attempts to serialize responses, resulting in 500 Internal Server Errors. The fix is straightforward: update all `NewsArticle` instantiations in `news_service.py` to use `description` instead of `summary`.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when `NewsService` creates `NewsArticle` objects with `summary` field instead of `description`
- **Property (P)**: The desired behavior - `NewsArticle` objects should be created with `description` field matching the schema definition
- **Preservation**: Existing news fetching, sentiment analysis, caching, and display behavior that must remain unchanged
- **NewsService**: The service class in `backend/app/services/news/news_service.py` that fetches news from Finnhub and NewsAPI
- **NewsArticle**: The Pydantic model in `backend/app/schemas/news.py` that defines the schema with `description` field
- **Field Mismatch**: The root cause where constructor parameter name doesn't match schema field name

## Bug Details

### Bug Condition

The bug manifests when the `NewsService.get_market_news()` or `NewsService.get_stock_news()` methods create `NewsArticle` objects. These methods use `summary=` as the parameter name when instantiating `NewsArticle`, but the Pydantic schema expects `description` as the field name. This causes validation to fail when FastAPI attempts to serialize the response.

**Formal Specification:**
```
FUNCTION isBugCondition(article_instantiation)
  INPUT: article_instantiation of type CodeStatement
  OUTPUT: boolean
  
  RETURN article_instantiation.class_name == "NewsArticle"
         AND article_instantiation.has_parameter("summary")
         AND NOT article_instantiation.has_parameter("description")
         AND schema_defines_field("NewsArticle", "description")
END FUNCTION
```

### Examples

- **Example 1**: In `get_stock_news()` at line 30, `NewsArticle(summary=item.get("summary", ""))` fails validation because schema expects `description`
- **Example 2**: In `get_market_news()` at line 52, `NewsArticle(summary=item.get("summary", ""))` fails validation for Finnhub articles
- **Example 3**: In `get_market_news()` at line 75, `NewsArticle(summary=item.get("description") or "")` fails validation for NewsAPI articles (uses correct source field but wrong parameter name)
- **Edge Case**: The `NewsAggregator` class in `aggregator.py` correctly uses `description=` in all normalization methods and does not exhibit this bug

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- News articles must continue to be fetched from Finnhub API with the same query parameters and response parsing
- News articles must continue to be fetched from NewsAPI with the same query parameters and response parsing
- Sentiment analysis using `_simple_sentiment()` must continue to calculate sentiment scores correctly
- Category classification using `_classify_category()` must continue to work correctly
- Article sorting by `published_at` descending must remain unchanged
- Article deduplication by title must remain unchanged
- Redis caching behavior (if implemented) must remain unchanged
- Frontend display of article summary/description text must remain unchanged

**Scope:**
All inputs that do NOT involve creating `NewsArticle` objects should be completely unaffected by this fix. This includes:
- API endpoint routing and request handling
- External API calls to Finnhub and NewsAPI
- Sentiment analysis logic
- Date formatting and timestamp conversion
- Error handling and logging
- Response serialization (will now succeed instead of fail)

## Hypothesized Root Cause

Based on the bug description and code analysis, the root cause is clear:

1. **Schema Evolution Without Service Update**: The `NewsArticle` schema was updated to use `description` field (likely to match industry-standard naming conventions), but the `NewsService` was not updated to reflect this change. The comment in `news.py` line 38 confirms this: `# Changed from summary to match design doc`

2. **Inconsistent Field Naming**: The service layer uses `summary` (which matches the Finnhub API response field name), while the schema uses `description` (which matches the NewsAPI response field name and is more standard)

3. **Missing Validation in Development**: The mismatch was not caught during development, suggesting either:
   - Tests were not run after the schema change
   - Tests don't cover the full serialization path
   - The change was made without updating all usages

4. **Partial Migration**: The `NewsAggregator` class correctly uses `description`, indicating that some parts of the codebase were updated but `NewsService` was missed

## Correctness Properties

Property 1: Bug Condition - Field Name Matches Schema

_For any_ `NewsArticle` instantiation in the codebase, the constructor SHALL use `description` as the parameter name (not `summary`), ensuring Pydantic validation succeeds when the API serializes responses.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - News Fetching Behavior

_For any_ news fetching operation (from Finnhub or NewsAPI), the fixed code SHALL produce exactly the same API calls, response parsing, sentiment analysis, and article content as the original code, preserving all existing functionality except for the field name used in object construction.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

The root cause is confirmed: field name mismatch between schema and service layer.

**File**: `backend/app/services/news/news_service.py`

**Function**: `get_stock_news()` (lines 14-40)

**Specific Changes**:
1. **Line 30**: Change `summary=item.get("summary", "")` to `description=item.get("summary", "")`
   - Note: We keep reading from `item.get("summary", "")` because that's the Finnhub API response field
   - We only change the parameter name from `summary=` to `description=`

**Function**: `get_market_news()` (lines 42-95)

**Specific Changes**:
2. **Line 52**: Change `summary=item.get("summary", "")` to `description=item.get("summary", "")`
   - For Finnhub articles in market news

3. **Line 75**: Change `summary=item.get("description") or ""` to `description=item.get("description") or ""`
   - For NewsAPI articles in market news
   - This one already reads from the correct source field (`description`), just needs parameter name fix

**No Changes Required**:
- `backend/app/services/news/aggregator.py` - Already uses `description` correctly in all normalization methods
- `backend/app/schemas/news.py` - Schema is correct as-is

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (validation errors), then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the field mismatch causes validation failures.

**Test Plan**: Write tests that call `get_market_news()` and `get_stock_news()` methods and attempt to serialize the results to JSON (simulating FastAPI response serialization). Run these tests on the UNFIXED code to observe Pydantic validation failures.

**Test Cases**:
1. **Market News Validation Test**: Call `get_market_news(limit=5)` and serialize to JSON (will fail on unfixed code with ValidationError)
2. **Stock News Validation Test**: Call `get_stock_news("RELIANCE", limit=5)` and serialize to JSON (will fail on unfixed code with ValidationError)
3. **API Endpoint Test**: Make HTTP GET request to `/api/v1/news/market` (will return 500 on unfixed code)
4. **Schema Inspection Test**: Verify that `NewsArticle` schema expects `description` field and does not have `summary` field

**Expected Counterexamples**:
- Pydantic ValidationError: "Field required" for `description` field
- HTTP 500 Internal Server Error from `/api/v1/news/market` endpoint
- Possible error message: "summary is not a valid field for NewsArticle"

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (NewsArticle instantiations), the fixed function produces the expected behavior (uses `description` field).

**Pseudocode:**
```
FOR ALL article_creation IN [get_market_news(), get_stock_news()] DO
  articles := article_creation()
  FOR EACH article IN articles DO
    ASSERT article.description IS NOT None
    ASSERT hasattr(article, "description")
    ASSERT article.model_dump() contains "description" key
    ASSERT article.model_dump() does NOT contain "summary" key
  END FOR
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (non-NewsArticle operations), the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL operation WHERE NOT creates_NewsArticle(operation) DO
  ASSERT original_behavior(operation) = fixed_behavior(operation)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for API calls, sentiment analysis, and article content, then write property-based tests capturing that behavior.

**Test Cases**:
1. **API Call Preservation**: Verify that Finnhub and NewsAPI are called with the same parameters before and after fix
2. **Content Preservation**: Verify that article title, url, source, published_at, and description content are identical before and after fix
3. **Sentiment Preservation**: Verify that sentiment analysis produces the same scores before and after fix
4. **Sorting Preservation**: Verify that articles are sorted in the same order before and after fix
5. **Deduplication Preservation**: Verify that the same articles are deduplicated before and after fix

### Unit Tests

- Test that `get_market_news()` returns articles with `description` field populated
- Test that `get_stock_news()` returns articles with `description` field populated
- Test that articles can be serialized to JSON without validation errors
- Test that `/api/v1/news/market` endpoint returns 200 OK response
- Test that article content matches the source API response (Finnhub `summary` or NewsAPI `description`)

### Property-Based Tests

- Generate random mock API responses and verify all articles have `description` field
- Generate random tickers and verify `get_stock_news()` always produces valid articles
- Test that article content is preserved across many scenarios (same text content, just different field name)
- Verify that sentiment scores remain consistent for the same article text before and after fix

### Integration Tests

- Test full flow: API request → NewsService → Pydantic validation → JSON response
- Test that frontend can successfully fetch and display market news
- Test that error toast no longer appears on news page load
- Test that article descriptions are displayed correctly in the UI
