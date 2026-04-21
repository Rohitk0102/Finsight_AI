import asyncio
import sys
import os
import yfinance as yf
from typing import List

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.supabase import supabase
from app.core.config import settings
from loguru import logger

# --- Ticker Universe ---
NSE_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS",
    "LICI.NS", "LT.NS", "HCLTECH.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    "ADANIENT.NS", "SUNPHARMA.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS",
    "ULTRACEMCO.NS", "BAJAJFINSV.NS", "ONGC.NS", "WIPRO.NS", "NTPC.NS",
    "JSWSTEEL.NS", "M&M.NS", "POWERGRID.NS", "ADANIPORTS.NS", "TATASTEEL.NS",
    "COALINDIA.NS", "TATA_CONSUMER.NS", "HINDALCO.NS", "GRASIM.NS", "SBILIFE.NS",
    "BAJAJ-AUTO.NS", "DRREDDY.NS", "HDFCLIFE.NS", "CIPLA.NS", "BRITANNIA.NS",
    "EICHERMOT.NS", "NESTLEIND.NS", "DIVISLAB.NS", "BPCL.NS", "APOLLOHOSP.NS",
    "HEROMOTOCO.NS", "TECHM.NS", "INDUSINDBK.NS", "UPL.NS", "ADANIPOWER.NS",
    # Next 50 and others
    "ZOMATO.NS", "HAL.NS", "TRENT.NS", "DLF.NS", "BEL.NS", "VBL.NS", "SIEMENS.NS",
    "ABB.NS", "CHOLAFIN.NS", "JIOFIN.NS", "TATAMTRDVR.NS", "SHREECEM.NS",
    "MARICO.NS", "BERGEPAINT.NS", "TVSMOTOR.NS", "COLPAL.NS", "PIDILITIND.NS",
    "HAVELLS.NS", "TATACONSUM.NS", "ICICIPRULI.NS", "GAIL.NS", "HINDPETRO.NS",
    "BOSCHLTD.NS", "SAMVARDHANA.NS", "JINDALSTEL.NS", "TATACOMM.NS"
]

US_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "V", "WMT", "XOM", "MA", "PG", "AVGO", "ORCL", "CVX", "HD", "KO", "PEP", "LLY",
    "ABBV", "MRK", "COST", "ADBE", "TMO", "PFE", "AVGO", "CSCO", "CRM", "ACN", "ABT",
    "LIN", "NKE", "DHR", "AMD", "TXN", "PM", "DIS", "INTC", "UPS", "MS", "RTX", "AMAT",
    "NEE", "CAT", "LOW", "HON", "AMGN", "GE", "UNP", "IBM", "DE", "INTU", "SBUX",
    "PLD", "GILD", "MDLZ", "ISRG", "BKNG", "AXP", "SYK", "TJX", "ADP", "VRTX", "LMT",
    "ADI", "MMC", "CVS", "AMT", "EL", "PYPL", "PANW", "SNPS", "REGN", "MDT", "ZTS",
    "CDNS", "MU", "KLAC", "LRCX", "CSX", "EQIX", "ADSK", "MELI", "MNST", "KDP", "MAR",
    "ORLY", "CTAS", "ROP", "MCHP", "IDXX", "PAYX", "PCAR", "CPRT", "DXCM", "AEP",
]

ALL_TICKERS = list(set(NSE_TICKERS + US_TICKERS))

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

async def fetch_and_save_metadata(tickers: List[str]):
    logger.info(f"Starting metadata sync for {len(tickers)} tickers...")
    
    count = 0
    for ticker in tickers:
        try:
            logger.info(f"Fetching {ticker}...")
            # Running yfinance in thread to avoid blocking loop
            def _fetch():
                t = yf.Ticker(ticker)
                return t.info
            
            info = await asyncio.to_thread(_fetch)
            if not info:
                logger.warning(f"No info for {ticker}")
                continue
                
            # Determine exchange
            exchange = "NSE" if ".NS" in ticker else "NASDAQ"
            if ".BO" in ticker: exchange = "BSE"
            if not exchange and "exchange" in info:
                exchange = info["exchange"]

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
            
            # Use asyncio.to_thread for Supabase execute() as it's blocking
            await asyncio.to_thread(
                supabase.table("stocks").upsert(stock_data, on_conflict="ticker").execute
            )
            count += 1
            if count % 10 == 0:
                logger.info(f"Synced {count}/{len(tickers)} stocks")
                
        except Exception as e:
            logger.error(f"Error syncing {ticker}: {e}")
            
    logger.info(f"Seeding complete. Synced {count} stocks.")

if __name__ == "__main__":
    asyncio.run(fetch_and_save_metadata(ALL_TICKERS))
