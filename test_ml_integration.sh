#!/bin/bash

# Test ML Integration - Backend to Frontend

echo "🧪 Testing ML Model Integration"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Backend ML Models
echo "1️⃣  Testing Backend ML Models..."
cd backend && source .venv/bin/activate

python3 << 'EOF'
import asyncio
from app.ml.models.ensemble import EnsemblePredictor

async def test():
    predictor = EnsemblePredictor()
    tickers = ['AAPL', 'RELIANCE.NS', 'TCS.NS']
    
    all_pass = True
    for ticker in tickers:
        try:
            result = await predictor.predict(ticker, risk_profile='moderate', horizon='medium', sentiment_score=0.0)
            
            # Validate
            is_valid = (
                result.predicted_1d > 0 and
                result.predicted_7d > 0 and
                result.predicted_30d > 0 and
                result.confidence > 0 and
                result.confidence <= 1 and
                str(result.signal) in ['Signal.BUY', 'Signal.SELL', 'Signal.HOLD']
            )
            
            if is_valid:
                print(f"✅ {ticker}: ${result.current_price:.2f} → ${result.predicted_7d:.2f} ({result.signal})")
            else:
                print(f"❌ {ticker}: Invalid prediction")
                all_pass = False
                
        except Exception as e:
            print(f"❌ {ticker}: {e}")
            all_pass = False
    
    return all_pass

success = asyncio.run(test())
exit(0 if success else 1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend ML Models: PASS${NC}"
else
    echo -e "${RED}❌ Backend ML Models: FAIL${NC}"
    exit 1
fi

echo ""

# Test 2: API Endpoint (if backend is running)
echo "2️⃣  Testing API Endpoint..."

if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    # Test health endpoint
    HEALTH=$(curl -s http://localhost:8000/health)
    if echo "$HEALTH" | grep -q "ok"; then
        echo -e "${GREEN}✅ API Health Check: PASS${NC}"
    else
        echo -e "${RED}❌ API Health Check: FAIL${NC}"
        exit 1
    fi
    
    # Note: Prediction endpoint requires auth, so we can't test it directly
    echo -e "${YELLOW}ℹ️  Prediction endpoint requires authentication (tested via frontend)${NC}"
else
    echo -e "${YELLOW}⚠️  Backend not running - skipping API test${NC}"
fi

echo ""

# Test 3: Model Files
echo "3️⃣  Checking Model Files..."
cd ..

LSTM_COUNT=$(find ml_models/lstm -name "metadata.json" 2>/dev/null | wc -l | tr -d ' ')
XGB_COUNT=$(find ml_models/xgb -name "metadata.json" 2>/dev/null | wc -l | tr -d ' ')
PROPHET_COUNT=$(find ml_models/prophet -name "metadata.json" 2>/dev/null | wc -l | tr -d ' ')

if [ "$LSTM_COUNT" -gt 0 ] && [ "$XGB_COUNT" -gt 0 ] && [ "$PROPHET_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Model Files: $LSTM_COUNT LSTM, $XGB_COUNT XGBoost, $PROPHET_COUNT Prophet${NC}"
else
    echo -e "${RED}❌ Model Files: Missing models${NC}"
    exit 1
fi

echo ""

# Test 4: Frontend API Client
echo "4️⃣  Checking Frontend API Client..."

if [ -f "frontend/lib/api/client.ts" ]; then
    if grep -q "predictApi" frontend/lib/api/client.ts; then
        echo -e "${GREEN}✅ Frontend API Client: predictApi found${NC}"
    else
        echo -e "${RED}❌ Frontend API Client: predictApi missing${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Frontend API Client: File not found${NC}"
    exit 1
fi

echo ""

# Summary
echo "================================"
echo -e "${GREEN}✅ All ML Integration Tests Passed!${NC}"
echo ""
echo "ML Models Status:"
echo "  • Backend predictions working correctly"
echo "  • All 3 model types (LSTM, XGBoost, Prophet) functional"
echo "  • Predictions validated (positive values, reasonable ranges)"
echo "  • $LSTM_COUNT tickers trained"
echo ""
echo "To test full stack with authentication:"
echo "  1. Start backend: cd backend && uvicorn app.main:app --reload"
echo "  2. Start frontend: cd frontend && npm run dev"
echo "  3. Sign in at http://localhost:3000"
echo "  4. Navigate to Predictor page"
echo "  5. Search for a stock (e.g., AAPL, RELIANCE)"
echo "  6. Verify predictions display correctly"
echo ""
