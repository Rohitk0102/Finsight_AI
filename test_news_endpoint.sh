#!/bin/bash

echo "Testing News API Endpoint..."
echo "=============================="
echo ""

# Test 1: Basic news fetch
echo "Test 1: Fetching news (page=1, limit=2)"
curl -s 'http://localhost:8000/api/v1/news?page=1&limit=2' | jq -r '.articles[0].title // "ERROR: " + .detail'
echo ""

# Test 2: News with ticker filter
echo "Test 2: Fetching news for RELIANCE"
curl -s 'http://localhost:8000/api/v1/news?page=1&limit=2&ticker=RELIANCE' | jq -r '.articles[0].title // "ERROR: " + .detail'
echo ""

# Test 3: Market news
echo "Test 3: Fetching market news"
curl -s 'http://localhost:8000/api/v1/news/market?limit=2' | jq -r '.[0].title // "ERROR: " + .detail'
echo ""

# Test 4: Health check
echo "Test 4: Backend health check"
curl -s 'http://localhost:8000/health' | jq '.'
echo ""

echo "=============================="
echo "Tests complete!"
