from app.tasks.celery_app import celery_app
from app.core.supabase import supabase
from app.services.data.stock_fetcher import StockDataFetcher
from app.core.security import decrypt_token
from app.services.broker.broker_factory import BrokerFactory
from loguru import logger
from datetime import datetime, timezone
import asyncio


import yfinance as yf
import math

def sanitize_num(val):
    if val is None:
        return None
    try:
        fval = float(val)
        if math.isnan(fval) or math.isinf(fval):
            return None
        return fval
    except (ValueError, TypeError):
        return None

TRACKED_TICKERS = [
    # NSE top 50
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "ITC.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TITAN.NS", "WIPRO.NS", "ULTRACEMCO.NS", "NESTLEIND.NS",
    "ADANIENT.NS", "JSWSTEEL.NS", "M&M.NS", "POWERGRID.NS", "ADANIPORTS.NS",
    "TATASTEEL.NS", "COALINDIA.NS", "TATA_CONSUMER.NS", "HINDALCO.NS", "GRASIM.NS",
    # US
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "V", "WMT",
    "JNJ", "XOM", "MA", "PG", "AVGO", "ORCL", "CVX", "HD", "KO", "PEP",
]


@celery_app.task(bind=True, max_retries=3)
def sync_stock_metadata(self):
    """Fetch and store fundamental metadata for tracked tickers."""
    success, failed = 0, 0
    for ticker in TRACKED_TICKERS:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            if not info:
                continue
            
            exchange = "NSE" if ".NS" in ticker else "NASDAQ"
            if ".BO" in ticker: exchange = "BSE"
            
            stock_data = {
                "ticker": ticker,
                "name": info.get("longName") or info.get("shortName") or ticker,
                "exchange": exchange,
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": sanitize_num(info.get("marketCap")),
                "pe_ratio": sanitize_num(info.get("trailingPE")),
                "eps": sanitize_num(info.get("trailingEps")),
                "isin": info.get("isin"),
            }
            supabase.table("stocks").upsert(stock_data, on_conflict="ticker").execute()
            success += 1
        except Exception as e:
            logger.error(f"Failed to sync metadata for {ticker}: {e}")
            failed += 1
    
    return {"success": success, "failed": failed}


@celery_app.task(bind=True, max_retries=3)
def sync_all_stocks(self):
    """Fetch and store daily OHLCV data for tracked tickers."""
    fetcher = StockDataFetcher()
    success, failed = 0, 0

    for ticker in TRACKED_TICKERS:
        try:
            data = asyncio.run(fetcher.get_ohlcv(ticker, period="5d", interval="1d"))
            rows = [
                {
                    "ticker": ticker,
                    "date": str(d.date),
                    "open": d.open,
                    "high": d.high,
                    "low": d.low,
                    "close": d.close,
                    "volume": d.volume,
                }
                for d in data
            ]
            if rows:
                supabase.table("ohlcv_daily").upsert(rows, on_conflict="ticker,date").execute()
            success += 1
        except Exception as e:
            logger.error(f"Failed to sync {ticker}: {e}")
            failed += 1

    logger.info(f"Data sync complete: {success} ok, {failed} failed")
    return {"success": success, "failed": failed}


@celery_app.task(bind=True, max_retries=2)
def sync_all_holdings(self):
    """Sync holdings for all active broker accounts."""
    accounts = (
        supabase.table("broker_accounts")
        .select("*")
        .eq("is_active", True)
        .execute()
    )

    for acc in accounts.data or []:
        try:
            access_token = decrypt_token(acc["access_token_encrypted"])
            broker = BrokerFactory.get_broker(acc["broker"])
            holdings = asyncio.run(broker.fetch_holdings(
                api_key=acc.get("api_key"),
                access_token=access_token,
            ))
            for h in holdings:
                h["user_id"] = acc["user_id"]
                h["broker_account_id"] = acc["id"]
            supabase.table("holdings").upsert(holdings, on_conflict="broker_account_id,ticker").execute()
            supabase.table("broker_accounts").update(
                {"last_synced_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", acc["id"]).execute()
        except Exception as e:
            logger.error(f"Holdings sync failed for account {acc['id']}: {e}")
