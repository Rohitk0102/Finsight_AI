# News Fetch Bug Fix

## Problem Summary

The news page was failing to load with two main errors:

1. **SSL Certificate Error**: `UNABLE_TO_VERIFY_LEAF_SIGNATURE` - Next.js proxy couldn't verify the self-signed certificate when proxying requests to `https://localhost:8000`
2. **Backend 500 Error**: News aggregator was throwing unhandled exceptions when external API providers failed

## Root Causes

### 1. SSL Certificate Verification Issue
- Next.js server-side proxy was rejecting self-signed certificates
- The `NODE_TLS_REJECT_UNAUTHORIZED=0` environment variable wasn't being applied to axios requests
- The Next.js rewrite proxy doesn't automatically inherit Node.js environment variables for HTTPS agent configuration

### 2. Backend Error Handling
- News aggregator providers (NewsAPI, GNews, Finnhub, Alpha Vantage, Marketaux) could fail due to:
  - Rate limits exceeded
  - Invalid API keys
  - Network timeouts
  - API-specific error responses
- Exception handling was too generic and didn't properly catch all error types
- API error responses (like rate limit messages) weren't being detected before parsing

## Fixes Applied

### Frontend Fixes

#### 1. Updated `frontend/lib/api/client.ts`
- Added HTTPS agent configuration for server-side requests
- Created custom HTTPS agent that accepts self-signed certificates in development
- This allows axios to make requests to `https://localhost:8000` without certificate validation errors

```typescript
const httpsAgent = typeof window === "undefined" && process.env.NODE_ENV !== "production"
  ? new https.Agent({
      rejectUnauthorized: false,
    })
  : undefined;
```

#### 2. Updated `frontend/next.config.mjs`
- Improved webpack configuration to handle Node.js modules properly
- Added fallbacks for `net` and `tls` modules
- Ensured the rewrite proxy has proper fallback URL

#### 3. Created `frontend/middleware.ts`
- Added Next.js middleware for future enhancements
- Provides a hook point for request/response manipulation if needed

### Backend Fixes

#### 1. Enhanced Error Handling in `backend/app/services/news/aggregator.py`

**Improved `_run_source` method:**
- Added specific exception handling for `httpx.TimeoutException`
- Added specific exception handling for `httpx.HTTPStatusError`
- Better logging with warning vs error levels
- More descriptive error messages in SourceFetchResult

**Enhanced API provider methods:**
- Added API-specific error response detection for each provider:
  - **NewsAPI**: Checks for `status: "error"` in response
  - **GNews**: Checks for `errors` array in response
  - **Finnhub**: Checks for `error` field in response
  - **Alpha Vantage**: Checks for `Error Message` or `Note` (rate limit indicator)
  - **Marketaux**: Checks for `error` object in response

- Removed redundant try-catch blocks that were hiding the actual error types
- Let httpx exceptions bubble up to be caught by the improved `_run_source` method

## How It Works Now

### Request Flow
1. Browser makes request to `/api/backend/news?page=1&limit=2`
2. Next.js rewrites to `https://localhost:8000/api/v1/news?page=1&limit=2`
3. Server-side axios uses custom HTTPS agent that accepts self-signed certificates
4. Backend receives request and calls news aggregator
5. News aggregator tries multiple providers in parallel
6. If some providers fail, others can still succeed (graceful degradation)
7. If all providers fail, returns 503 with clear error message
8. If at least one provider succeeds, returns articles with warning logged

### Error Handling Strategy
- **Partial failures**: If some providers fail but others succeed, return available articles
- **Complete failures**: If all providers fail, return 503 with descriptive error
- **Timeout handling**: 10-second timeout per provider, logged as warning
- **Rate limit detection**: API-specific error messages are detected and logged
- **Network errors**: Caught and logged with provider name

## Testing

### Test the fix:
1. Restart the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --ssl-keyfile ../certs/localhost.key --ssl-certfile ../certs/localhost.crt
   ```

2. Restart the frontend server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Navigate to `https://localhost:3000/news`
4. The news should load without SSL errors

### Expected Behavior:
- ✅ News articles load successfully
- ✅ No SSL certificate errors in browser console
- ✅ No 500 errors from backend
- ✅ If some providers fail, articles from working providers still display
- ✅ If all providers fail, user sees clear error message (503)

## API Provider Status

The following providers are configured with valid API keys:
- ✅ NewsAPI (key: `6432b7f2553343098d539c6ae21db21b`)
- ✅ GNews (key: `16a96af9dacd91ec5249f66449ab00d5`)
- ✅ Finnhub (key: `d7af541r01qn9i7kn3f0d7af541r01qn9i7kn3fg`)
- ✅ Alpha Vantage (key: `ZK25SE8AO2IVMCLA`)
- ✅ Marketaux (key: `SDjTI8dFtO7RZP62NysAEcmoB9mb5oTMOq5tcuGI`)

**Note**: Free tier API keys have rate limits. If you see 503 errors, it may be due to rate limit exhaustion. The system will automatically retry with other providers.

## Monitoring

Check backend logs for provider status:
```bash
# Look for these log patterns:
# Success: "Fetched X articles from [Provider] for query: Y"
# Warning: "Timeout fetching from [Provider]"
# Warning: "HTTP error fetching from [Provider]"
# Error: "Unexpected error fetching from [Provider]"
```

## Future Improvements

1. **Caching**: Implement Redis caching for news articles (already in place, TTL: 300s)
2. **Rate Limit Tracking**: Track API usage per provider to avoid hitting limits
3. **Provider Health Monitoring**: Dashboard showing which providers are working
4. **Fallback Content**: Show cached content when all providers are down
5. **Provider Priority**: Prioritize faster/more reliable providers
