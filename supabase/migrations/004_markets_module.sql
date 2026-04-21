-- ============================================================
-- Finsight AI — Market Pulse module tables
-- Run after 003_phase2_schema.sql
-- ============================================================

create table if not exists market_watchlists (
  id          uuid primary key default uuid_generate_v4(),
  user_id     text not null references user_profiles(clerk_id) on delete cascade,
  symbol      text not null,
  exchange    text not null default 'NSE',
  notes       text,
  created_at  timestamptz not null default now(),
  unique (user_id, symbol)
);

create index if not exists idx_market_watchlists_user_created
  on market_watchlists(user_id, created_at desc);

create table if not exists market_recent_views (
  id             uuid primary key default uuid_generate_v4(),
  user_id        text not null references user_profiles(clerk_id) on delete cascade,
  symbol         text not null,
  last_viewed_at timestamptz not null default now(),
  unique (user_id, symbol)
);

create index if not exists idx_market_recent_views_user_last_viewed
  on market_recent_views(user_id, last_viewed_at desc);

create table if not exists market_article_bookmarks (
  id           uuid primary key default uuid_generate_v4(),
  user_id      text not null references user_profiles(clerk_id) on delete cascade,
  article_id   text not null,
  title        text not null,
  source       text,
  source_url   text not null,
  published_at timestamptz not null,
  created_at   timestamptz not null default now(),
  unique (user_id, source_url)
);

create index if not exists idx_market_bookmarks_user_published
  on market_article_bookmarks(user_id, published_at desc);

create table if not exists market_price_alerts (
  id              uuid primary key default uuid_generate_v4(),
  user_id         text not null references user_profiles(clerk_id) on delete cascade,
  symbol          text not null,
  exchange        text not null default 'NSE',
  alert_type      text not null check (alert_type in ('price_above', 'price_below', 'pct_change')),
  threshold_value numeric(15, 4) not null,
  is_active       boolean not null default true,
  created_at      timestamptz not null default now()
);

create index if not exists idx_market_alerts_user_symbol
  on market_price_alerts(user_id, symbol, created_at desc);
