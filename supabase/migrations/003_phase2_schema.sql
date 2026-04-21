-- ============================================================
-- Finsight AI — Phase 2 Schema: ML signals + backtesting
-- Run in Supabase SQL Editor after 001_initial_schema.sql
-- ============================================================

-- ── Extend predictions table ──────────────────────────────────────────────────
-- Add columns needed for full prediction lifecycle + backtesting resolution

alter table predictions
  add column if not exists predicted_price       numeric(15, 4),
  add column if not exists current_price_at_pred numeric(15, 4),
  add column if not exists horizon_days          int not null default 7
                             check (horizon_days in (1, 7, 30)),
  add column if not exists model_version         text,
  -- Backtesting resolution (populated by Celery task, not on insert)
  add column if not exists actual_price          numeric(15, 4),
  add column if not exists direction_correct     boolean,
  add column if not exists mape                  numeric(8, 4),
  add column if not exists resolved_at           timestamptz;

-- Index for fast unresolved-prediction queries
create index if not exists idx_predictions_unresolved
  on predictions(ticker, horizon_days, created_at)
  where resolved_at is null;

-- ── Ticker sentiment cache ────────────────────────────────────────────────────
-- Pre-computed FinBERT sentiment scores (populated by nightly Celery task)

create table if not exists ticker_sentiment (
  ticker          text primary key,
  sentiment_score numeric(5, 4) not null,   -- -1.0 to +1.0
  confidence      numeric(5, 4) not null,
  news_count      int not null default 0,
  updated_at      timestamptz not null default now()
);

-- ── Model accuracy summary ────────────────────────────────────────────────────
-- Materialized per-ticker per-horizon accuracy, refreshed by Celery daily

create table if not exists model_accuracy (
  id            uuid primary key default uuid_generate_v4(),
  ticker        text not null,
  horizon_days  int not null check (horizon_days in (1, 7, 30)),
  model_version text not null,
  hit_rate      numeric(5, 4),   -- % predictions with correct direction
  avg_mape      numeric(8, 4),   -- mean absolute percentage error
  n_samples     int not null default 0,
  computed_at   timestamptz not null default now(),
  unique (ticker, horizon_days, model_version)
);

create index if not exists idx_model_accuracy_ticker
  on model_accuracy(ticker, horizon_days, computed_at desc);
