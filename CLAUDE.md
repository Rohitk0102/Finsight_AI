# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Finsight AI is a production-level AI stock prediction and portfolio management platform. It predicts stock price movements using an ensemble of ML models (LSTM + XGBoost + Prophet), provides real-time news with FinBERT sentiment analysis, and integrates with Indian broker APIs (Zerodha, Upstox, Angel One) for a unified portfolio dashboard.

## Commands

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run API server
uvicorn app.main:app --reload --port 8000

# Run Celery worker (background data sync + model retraining)
celery -A app.tasks.celery_app worker --loglevel=info

# Run Celery beat scheduler
celery -A app.tasks.celery_app beat --loglevel=info
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev          # dev server on :3000
npm run build        # production build
npm run type-check   # TypeScript check
npm run lint
```

### Full stack via Docker

```bash
cp .env.example .env   # fill in keys first
docker-compose up --build
```

### Database

Apply migration in Supabase SQL editor: `supabase/migrations/001_initial_schema.sql`

## Architecture

```
backend/app/
  main.py              — FastAPI app, middleware, lifespan
  core/
    config.py          — Pydantic Settings (all env vars)
    supabase.py        — Supabase client (service-role + anon)
    redis.py           — Async Redis helpers (get/set/delete)
    security.py        — JWT, password hashing, Fernet encryption for broker tokens
    dependencies.py    — FastAPI dependencies: get_current_user, rate_limit
  api/routes/
    auth.py            — signup, login, logout, /me
    stocks.py          — search, detail, OHLCV, live price
    predict.py         — ensemble prediction, portfolio analysis
    news.py            — market news, ticker news, sentiment
    portfolio.py       — holdings, transactions, broker sync
    broker.py          — OAuth callbacks (Upstox), Zerodha session, Angel One
    screener.py        — stock screener, watchlist CRUD
  ml/
    models/ensemble.py — EnsemblePredictor: XGBoost + Prophet + LSTM → weighted average
    utils/feature_engineering.py — pandas-ta indicators on OHLCV DataFrames
  services/
    data/stock_fetcher.py    — yfinance wrapper (search, OHLCV, live price, screener)
    news/news_service.py     — Finnhub news + rule-based sentiment (→ swap for FinBERT)
    broker/
      zerodha_broker.py      — kiteconnect SDK
      upstox_broker.py       — Upstox v2 REST API
      angelone_broker.py     — SmartAPI SDK
      groww_broker.py        — CSV import only (no official API)
      broker_factory.py      — factory pattern for broker dispatch
  tasks/
    celery_app.py      — Celery config + beat schedule (data sync daily, model retrain weekly)
    data_sync.py       — sync OHLCV for tracked tickers + all broker holdings
    model_retrain.py   — delete cached .pkl files + retrain XGBoost

frontend/
  app/
    sign-in/, sign-up/  — Clerk hosted auth pages
    dashboard/         — portfolio summary + AI analysis cards
    predictor/         — stock search → ensemble prediction display
    news/              — Finnhub news feed with sentiment badges
    portfolio/         — holdings table + broker connect/sync/unlink
    screener/          — stock screener with watchlist
    settings/          — broker connection forms
  lib/api/client.ts    — axios client with Clerk JWT interceptor + typed API functions
  middleware.ts        — Clerk route protection (protected app sections)
  lib/utils.ts         — formatCurrency, formatPercent, getSignalColor, getRiskColor

supabase/migrations/001_initial_schema.sql — All tables + RLS policies + triggers
```

## Key Design Decisions

- **Broker token storage**: Encrypted with Fernet (AES-256) before storing in `broker_accounts.access_token_encrypted`. Key comes from `BROKER_TOKEN_ENCRYPTION_KEY` env var.
- **Prediction caching**: Redis key `predict:{ticker}:{risk_profile}:{horizon}` — 1 hour TTL. XGBoost models cached as `.pkl` files in `ml_models/`.
- **Rate limiting**: Sliding window via Redis `INCR` + `EXPIRE` in `core/dependencies.py:rate_limit()`.
- **ML ensemble weights**: XGBoost 40%, Prophet 35%, LSTM 25%. LSTM is trained on-the-fly (50 epochs) if no cached model exists — in production replace with pre-trained weights.
- **News sentiment**: `services/news/news_service.py:_simple_sentiment()` is a keyword-based fallback. For production replace with FinBERT: `transformers.pipeline("text-classification", model="ProsusAI/finbert")`.
- **Groww**: Has no official API. Only CSV import is supported via `groww_broker.py:import_from_csv()`.
- **RLS**: Auth is enforced in FastAPI using Clerk JWT verification. Database access is via Supabase `service_role` key.
- **Celery beat schedule**: Data sync at 4:30pm IST (market close), model retrain weekly Sunday midnight, broker holdings sync every 4 hours.

## Environment Variables

Copy `.env.example` to `.env` for backend. Copy frontend env vars to `frontend/.env.local`.
Required before running: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `CLERK_JWKS_URL`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `BROKER_TOKEN_ENCRYPTION_KEY`, `FINNHUB_API_KEY`.

Generate Fernet key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
