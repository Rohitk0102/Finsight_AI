import re
import yfinance as yf
from typing import List
from loguru import logger
import asyncio

COMMON_FALSE_POSITIVES = {
    "A", "I", "AI", "AN", "THE", "IS", "IT", "TO", "OF", "IN", "ON", "AT", 
    "BY", "FOR", "WITH", "AS", "SO", "OR", "IF", "BE", "DO", "UP", "HE", "WE", "US", "AM", "ME",
    "MY", "NO", "GO", "HI", "OH", "OK", "BUY", "SELL", "HOLD", "CALL", "PUT", "ETF", "FED", "CEO", "CEO"
}

# Cache for ticker validation to avoid redundant slow yfinance lookups
_TICKER_VALIDATION_CACHE = {}

def _is_valid_ticker_sync(ticker: str) -> bool:
    if ticker in _TICKER_VALIDATION_CACHE:
        return _TICKER_VALIDATION_CACHE[ticker]
    
    try:
        t = yf.Ticker(ticker)
        # Fast check if it exists: 'currentPrice' or 'regularMarketPrice' usually in fast_info
        # .info can be slow. fast_info is better in yfinance >= 0.2.0
        is_valid = 'currentPrice' in t.fast_info or 'regularMarketPrice' in t.info or 'symbol' in t.info
        _TICKER_VALIDATION_CACHE[ticker] = is_valid
        return is_valid
    except Exception as e:
        logger.debug(f"Ticker validation failed for {ticker}: {e}")
        return False

async def extract_tickers(text: str) -> List[str]:
    """
    Extracts uppercase 1-5 char symbols from text,
    filters common false positives, and validates against yfinance in parallel.
    """
    # Exclude common small words and single letters
    candidates = re.findall(r'\b[A-Z]{2,5}\b', text)
    unique_candidates = list(set(candidates))
    
    tasks = []
    for cand in unique_candidates:
        if cand in COMMON_FALSE_POSITIVES:
            continue
        # Validate in parallel
        tasks.append(asyncio.to_thread(_is_valid_ticker_sync, cand))
            
    results = await asyncio.gather(*tasks)
    
    valid_tickers = []
    for cand, is_valid in zip([c for c in unique_candidates if c not in COMMON_FALSE_POSITIVES], results):
        if is_valid:
            valid_tickers.append(cand)
            
    return valid_tickers
