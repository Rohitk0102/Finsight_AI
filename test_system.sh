#!/bin/bash

# Finsight AI - System Health Check Script
# This script tests all major components of the system

set -e  # Exit on error

echo "🚀 Finsight AI - System Health Check"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print section header
section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================
# 1. Check Prerequisites
# ============================================
section "1. Checking Prerequisites"

if command_exists node; then
    NODE_VERSION=$(node --version)
    success "Node.js installed: $NODE_VERSION"
else
    error "Node.js not found"
    exit 1
fi

if command_exists npm; then
    NPM_VERSION=$(npm --version)
    success "npm installed: $NPM_VERSION"
else
    error "npm not found"
    exit 1
fi

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    success "Python installed: $PYTHON_VERSION"
else
    error "Python 3 not found"
    exit 1
fi

if command_exists redis-cli; then
    if redis-cli ping > /dev/null 2>&1; then
        success "Redis is running"
    else
        warning "Redis is not responding (may need to start it)"
    fi
else
    warning "redis-cli not found (Redis may not be installed)"
fi

# ============================================
# 2. Check Environment Files
# ============================================
section "2. Checking Environment Files"

if [ -f "backend/.env" ]; then
    success "Backend .env file exists"
    
    # Check for required variables
    if grep -q "SUPABASE_URL=" backend/.env; then
        success "  SUPABASE_URL configured"
    else
        error "  SUPABASE_URL missing"
    fi
    
    if grep -q "CLERK_JWKS_URL=" backend/.env; then
        success "  CLERK_JWKS_URL configured"
    else
        error "  CLERK_JWKS_URL missing"
    fi
    
    if grep -q "BROKER_TOKEN_ENCRYPTION_KEY=" backend/.env; then
        success "  BROKER_TOKEN_ENCRYPTION_KEY configured"
    else
        error "  BROKER_TOKEN_ENCRYPTION_KEY missing"
    fi
else
    error "Backend .env file not found"
fi

if [ -f "frontend/.env.local" ]; then
    success "Frontend .env.local file exists"
    
    if grep -q "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=" frontend/.env.local; then
        success "  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY configured"
    else
        error "  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY missing"
    fi
else
    error "Frontend .env.local file not found"
fi

# ============================================
# 3. Check Backend Dependencies
# ============================================
section "3. Checking Backend Dependencies"

if [ -d "backend/.venv" ]; then
    success "Python virtual environment exists"
    
    # Activate venv and check key packages
    source backend/.venv/bin/activate
    
    if python -c "import fastapi" 2>/dev/null; then
        success "  FastAPI installed"
    else
        error "  FastAPI not installed"
    fi
    
    if python -c "import celery" 2>/dev/null; then
        success "  Celery installed"
    else
        error "  Celery not installed"
    fi
    
    if python -c "import torch" 2>/dev/null; then
        success "  PyTorch installed"
    else
        warning "  PyTorch not installed (needed for LSTM)"
    fi
    
    if python -c "import xgboost" 2>/dev/null; then
        success "  XGBoost installed"
    else
        warning "  XGBoost not installed"
    fi
    
    deactivate
else
    error "Python virtual environment not found"
    echo "  Run: cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

# ============================================
# 4. Check Frontend Dependencies
# ============================================
section "4. Checking Frontend Dependencies"

if [ -d "frontend/node_modules" ]; then
    success "Frontend node_modules exists"
else
    error "Frontend node_modules not found"
    echo "  Run: cd frontend && npm install"
fi

# ============================================
# 5. Check ML Models
# ============================================
section "5. Checking ML Models"

if [ -d "ml_models" ]; then
    success "ml_models directory exists"
    
    LSTM_COUNT=$(find ml_models/lstm -name "metadata.json" 2>/dev/null | wc -l | tr -d ' ')
    XGB_COUNT=$(find ml_models/xgb -name "metadata.json" 2>/dev/null | wc -l | tr -d ' ')
    PROPHET_COUNT=$(find ml_models/prophet -name "metadata.json" 2>/dev/null | wc -l | tr -d ' ')
    
    success "  LSTM models: $LSTM_COUNT tickers"
    success "  XGBoost models: $XGB_COUNT tickers"
    success "  Prophet models: $PROPHET_COUNT tickers"
    
    if [ "$LSTM_COUNT" -eq 0 ]; then
        warning "  No LSTM models trained yet"
    fi
else
    warning "ml_models directory not found (will be created on first training)"
fi

# ============================================
# 6. Check Running Processes
# ============================================
section "6. Checking Running Processes"

if pgrep -f "celery.*worker" > /dev/null; then
    WORKER_PID=$(pgrep -f "celery.*worker" | head -1)
    success "Celery worker is running (PID: $WORKER_PID)"
else
    warning "Celery worker is not running"
    echo "  Start with: cd backend && celery -A app.tasks.celery_app worker --loglevel=info"
fi

if pgrep -f "celery.*beat" > /dev/null; then
    BEAT_PID=$(pgrep -f "celery.*beat" | head -1)
    success "Celery beat is running (PID: $BEAT_PID)"
else
    warning "Celery beat is not running"
    echo "  Start with: cd backend && celery -A app.tasks.celery_app beat --loglevel=info"
fi

if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    UVICORN_PID=$(pgrep -f "uvicorn.*app.main:app" | head -1)
    success "FastAPI server is running (PID: $UVICORN_PID)"
else
    warning "FastAPI server is not running"
    echo "  Start with: cd backend && uvicorn app.main:app --reload --port 8000"
fi

if pgrep -f "next-server" > /dev/null || pgrep -f "node.*next" > /dev/null; then
    success "Next.js dev server is running"
else
    warning "Next.js dev server is not running"
    echo "  Start with: cd frontend && npm run dev"
fi

# ============================================
# 7. Test API Endpoints (if backend is running)
# ============================================
section "7. Testing API Endpoints"

if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    # Test health endpoint
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        success "Health endpoint responding"
    else
        error "Health endpoint not responding"
    fi
    
    # Test API docs
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        success "API docs accessible"
    else
        error "API docs not accessible"
    fi
else
    warning "Backend not running, skipping API tests"
fi

# ============================================
# 8. Check Frontend Build
# ============================================
section "8. Checking Frontend"

cd frontend

# Check for TypeScript errors (in our code only)
echo "Running TypeScript check..."
if npm run type-check 2>&1 | grep -v "node_modules" | grep -q "error TS"; then
    warning "TypeScript errors found (check output above)"
else
    success "No TypeScript errors in application code"
fi

# Check for linting errors
echo "Running ESLint..."
if npm run lint > /dev/null 2>&1; then
    success "No linting errors"
else
    warning "Linting errors found"
fi

cd ..

# ============================================
# 9. Summary
# ============================================
section "Summary"

echo ""
echo "System health check complete!"
echo ""
echo "Next steps:"
echo "1. If any services are not running, start them using the commands shown above"
echo "2. Apply Phase 2 database migration (see apply_phase2_migration.md)"
echo "3. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000/docs"
echo "   - Health check: http://localhost:8000/health"
echo ""
echo "For detailed deployment instructions, see DEPLOYMENT_CHECKLIST.md"
echo ""
