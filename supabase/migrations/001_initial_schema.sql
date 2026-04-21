-- ============================================================
-- Finsight AI — Initial Schema
-- Auth: Clerk (user identity stored as clerk_id text)
-- DB:   Supabase (service-role access only — no RLS on auth.users)
-- Run this in Supabase SQL Editor or via supabase db push
-- ============================================================

-- Enable necessary extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ── User profiles ─────────────────────────────────────────────────────────────
-- Primary key is the Clerk user ID (e.g. user_2abc123)
create table if not exists user_profiles (
  clerk_id          text primary key,          -- Clerk user ID
  email             text not null,
  full_name         text,
  risk_profile      text not null default 'moderate'
                      check (risk_profile in ('conservative', 'moderate', 'aggressive')),
  investment_horizon text not null default 'medium'
                      check (investment_horizon in ('short', 'medium', 'long')),
  preferred_sectors  text[] default '{}',
  investment_amount  numeric(15, 2),
  created_at        timestamptz default now(),
  updated_at        timestamptz default now()
);

-- ── Broker accounts ───────────────────────────────────────────────────────────
create table if not exists broker_accounts (
  id                      uuid primary key default uuid_generate_v4(),
  user_id                 text not null references user_profiles(clerk_id) on delete cascade,
  broker                  text not null
                            check (broker in ('zerodha', 'upstox', 'angel_one', 'groww')),
  account_id              text,
  display_name            text,
  api_key                 text,
  access_token_encrypted  text,        -- AES-256 encrypted
  is_active               boolean not null default true,
  last_synced_at          timestamptz,
  created_at              timestamptz default now(),
  unique (user_id, broker)
);

-- ── Holdings ──────────────────────────────────────────────────────────────────
create table if not exists holdings (
  id                  uuid primary key default uuid_generate_v4(),
  user_id             text not null references user_profiles(clerk_id) on delete cascade,
  broker_account_id   uuid not null references broker_accounts(id) on delete cascade,
  ticker              text not null,
  name                text,
  quantity            numeric(15, 6) not null,
  average_price       numeric(15, 4) not null,
  current_price       numeric(15, 4) not null default 0,
  current_value       numeric(15, 4) not null default 0,
  invested_value      numeric(15, 4) not null default 0,
  unrealized_pnl      numeric(15, 4) not null default 0,
  unrealized_pnl_pct  numeric(10, 4) not null default 0,
  day_change          numeric(15, 4) default 0,
  day_change_pct      numeric(10, 4) default 0,
  last_updated        timestamptz default now(),
  unique (broker_account_id, ticker)
);

-- ── Transactions ──────────────────────────────────────────────────────────────
create table if not exists transactions (
  id                  uuid primary key default uuid_generate_v4(),
  user_id             text not null references user_profiles(clerk_id) on delete cascade,
  broker_account_id   uuid references broker_accounts(id) on delete set null,
  ticker              text not null,
  transaction_type    text not null check (transaction_type in ('BUY', 'SELL')),
  quantity            numeric(15, 6) not null,
  price               numeric(15, 4) not null,
  total_value         numeric(15, 4) not null,
  transaction_date    timestamptz not null,
  charges             numeric(10, 4) default 0,
  notes               text,
  created_at          timestamptz default now()
);

-- ── Stocks metadata ───────────────────────────────────────────────────────────
create table if not exists stocks (
  ticker        text primary key,
  name          text,
  exchange      text,
  sector        text,
  industry      text,
  market_cap    numeric(20, 2),
  pe_ratio      numeric(10, 4),
  eps           numeric(10, 4),
  isin          text,
  updated_at    timestamptz default now()
);

-- ── OHLCV daily data ──────────────────────────────────────────────────────────
create table if not exists ohlcv_daily (
  id      bigserial primary key,
  ticker  text not null,
  date    date not null,
  open    numeric(15, 4),
  high    numeric(15, 4),
  low     numeric(15, 4),
  close   numeric(15, 4),
  volume  bigint,
  unique (ticker, date)
);

create index if not exists idx_ohlcv_ticker_date on ohlcv_daily(ticker, date desc);

-- ── Predictions ───────────────────────────────────────────────────────────────
create table if not exists predictions (
  id              uuid primary key default uuid_generate_v4(),
  user_id         text references user_profiles(clerk_id) on delete set null,
  ticker          text not null,
  signal          text not null check (signal in ('BUY', 'SELL', 'HOLD')),
  confidence      numeric(5, 4),
  risk_score      numeric(5, 2),
  predicted_7d    numeric(15, 4),
  risk_profile    text,
  horizon         text,
  created_at      timestamptz default now()
);

create index if not exists idx_predictions_user_ticker on predictions(user_id, ticker, created_at desc);

-- ── News articles ─────────────────────────────────────────────────────────────
create table if not exists news_articles (
  id              text primary key,
  ticker          text,
  title           text not null,
  summary         text,
  url             text,
  source          text,
  published_at    timestamptz,
  sentiment       text check (sentiment in ('positive', 'negative', 'neutral')),
  sentiment_score numeric(5, 4),
  category        text,
  image_url       text,
  created_at      timestamptz default now()
);

create index if not exists idx_news_ticker_pub on news_articles(ticker, published_at desc);

-- ── Watchlists ────────────────────────────────────────────────────────────────
create table if not exists watchlists (
  id         uuid primary key default uuid_generate_v4(),
  user_id    text not null references user_profiles(clerk_id) on delete cascade,
  ticker     text not null,
  created_at timestamptz default now(),
  unique (user_id, ticker)
);

-- ── Alert configurations ──────────────────────────────────────────────────────
create table if not exists alert_configurations (
  id              uuid primary key default uuid_generate_v4(),
  user_id         text not null references user_profiles(clerk_id) on delete cascade,
  ticker          text not null,
  alert_type      text not null check (alert_type in ('price_above', 'price_below', 'signal_change', 'news_alert')),
  threshold_value numeric(15, 4),
  is_active       boolean default true,
  last_triggered  timestamptz,
  created_at      timestamptz default now()
);

-- ============================================================
-- No RLS — authorization is enforced by the FastAPI backend
-- using the Clerk JWT. The backend uses the service-role key
-- which bypasses Supabase RLS entirely.
-- ============================================================

-- ohlcv and stocks are public read (no user context needed)
alter table ohlcv_daily enable row level security;
alter table stocks enable row level security;

create policy "Public read OHLCV"
  on ohlcv_daily for select using (true);

create policy "Public read stocks"
  on stocks for select using (true);

-- ============================================================
-- Triggers: updated_at auto-update
-- ============================================================

create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trg_user_profiles_updated_at
  before update on user_profiles
  for each row execute function update_updated_at();
