# Implementation Plan

- [ ] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Field Name Mismatch Causes Validation Failure
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists (Pydantic ValidationError)
  - **Scoped PBT Approach**: Scope the property to concrete failing cases - NewsArticle instantiations with `summary=` parameter
  - Test that `get_market_news()` and `get_stock_news()` create NewsArticle objects that can be serialized to JSON without ValidationError
  - The test assertions should verify that articles have `description` field (not `summary`) and can be serialized successfully
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS with Pydantic ValidationError (this is correct - it proves the bug exists)
  - Document counterexamples found: "NewsArticle instantiation with summary= parameter causes ValidationError: Field required for description"
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - News Fetching Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for API calls, sentiment analysis, and article content
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - API calls to Finnhub and NewsAPI use same parameters
    - Article content (title, url, source, published_at, description text) is identical
    - Sentiment analysis produces same scores
    - Articles are sorted by published_at descending
    - Articles are deduplicated by title
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 3. Fix for field name mismatch in NewsService

  - [ ] 3.1 Implement the fix
    - Update `backend/app/services/news/news_service.py` line 30 in `get_stock_news()`: change `summary=item.get("summary", "")` to `description=item.get("summary", "")`
    - Update `backend/app/services/news/news_service.py` line 52 in `get_market_news()`: change `summary=item.get("summary", "")` to `description=item.get("summary", "")` (Finnhub articles)
    - Update `backend/app/services/news/news_service.py` line 75 in `get_market_news()`: change `summary=item.get("description") or ""` to `description=item.get("description") or ""` (NewsAPI articles)
    - _Bug_Condition: isBugCondition(article_instantiation) where article_instantiation.class_name == "NewsArticle" AND article_instantiation.has_parameter("summary") AND NOT article_instantiation.has_parameter("description")_
    - _Expected_Behavior: NewsArticle objects SHALL be created with description= parameter matching the schema definition_
    - _Preservation: News fetching, sentiment analysis, caching, sorting, and deduplication behavior SHALL remain unchanged_
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Field Name Matches Schema
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - News Fetching Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
