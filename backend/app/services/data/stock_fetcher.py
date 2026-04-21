"""
Resilient stock data fetcher.
Implements a multi-provider fallback strategy (Finnhub, Alpha Vantage, Marketaux, yfinance)
to ensure high availability and performance for Indian and Global markets.
"""
import asyncio
import warnings
# Suppress yfinance/pandas noise
warnings.filterwarnings("ignore", message=".*Pandas4Warning.*")
warnings.filterwarnings("ignore", category=FutureWarning)

import yfinance as yf
import pandas as pd
from typing import Optional, List, Any, Dict
from app.schemas.stock import StockDetail, OHLCVData, StockSearchResult
from app.core.config import settings
import httpx
import requests
from requests import Session
from loguru import logger
from datetime import datetime, timezone


class StockDataFetcher:
    def __init__(self):
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self.fast_timeout = httpx.Timeout(5.0, connect=2.0)
        self.verify_ssl = settings.ENVIRONMENT != "development"
        self.session = Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    async def search_stocks(self, query: str, exchange: Optional[str] = None) -> List[StockSearchResult]:
        """
        Search tickers via multiple providers with parallel fetching.
        """
        tasks = []
        if settings.FINNHUB_API_KEY:
            tasks.append(self._search_finnhub(query, exchange))
        
        if settings.FMP_API_KEY:
            tasks.append(self._search_fmp(query, exchange))
        
        # Parallel search
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)
        
        flattened: List[StockSearchResult] = []
        for res in results_nested:
            if isinstance(res, list):
                flattened.extend(res)
            elif isinstance(res, Exception):
                logger.warning(f"Search provider failed: {res}")

        # Fallback to local heuristic if no results
        if not flattened:
            return await self._search_fallback(query)
            
        # Deduplicate
        seen = set()
        unique = []
        for item in flattened:
            if item.ticker not in seen:
                unique.append(item)
                seen.add(item.ticker)
        
        return unique[:15]

    async def _search_finnhub(self, query: str, exchange: Optional[str] = None) -> List[StockSearchResult]:
        url = f"https://finnhub.io/api/v1/search?q={query}&token={settings.FINNHUB_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("result", [])[:15]:
                # For Indian markets, Finnhub might use .NS or .BO
                ticker = item["symbol"]
                if exchange and exchange.upper() not in item.get("exchange", "").upper():
                    # Optimization: if searching for NSE but got US, skip unless query is exact match
                    if exchange.upper() == "NSE" and "." not in ticker:
                        continue
                
                results.append(StockSearchResult(
                    ticker=ticker,
                    name=item["description"],
                    exchange=item.get("exchange", ""),
                    sector=None,
                    industry=None,
                ))
            return results
        except Exception as e:
            logger.error(f"Finnhub search error: {e}")
            return []

    async def _search_fmp(self, query: str, exchange: Optional[str] = None) -> List[StockSearchResult]:
        """Search tickers using Financial Modeling Prep."""
        url = f"https://financialmodelingprep.com/api/v3/search?query={query}&limit=15&apikey={settings.FMP_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data:
                ticker = item.get("symbol", "")
                exch = item.get("exchangeShortName", "")
                
                # Filter by exchange if provided
                if exchange and exchange.upper() not in exch.upper():
                    # Special handling for Indian exchanges in FMP
                    if exchange.upper() == "NSE" and exch.upper() != "NSE":
                        continue
                    if exchange.upper() == "BSE" and exch.upper() != "BSE":
                        continue

                results.append(StockSearchResult(
                    ticker=ticker,
                    name=item.get("name", ""),
                    exchange=exch,
                    sector=item.get("sector"),
                    industry=None,
                ))
            return results
        except Exception as e:
            logger.error(f"FMP search error: {e}")
            return []

    async def _search_fallback(self, query: str) -> List[StockSearchResult]:
        # Simple local search in a limited universe could go here
        return []

    async def get_stock_detail(self, ticker: str) -> Optional[StockDetail]:
        """
        Fetch full stock detail with fallback chain.
        1. yfinance (comprehensive info)
        2. Alpha Vantage (fundamental stats)
        3. Multi-provider price augmentation
        """
        detail = await self._get_detail_yfinance(ticker)
        
        if not detail and settings.ALPHA_VANTAGE_API_KEY:
            logger.info(f"yfinance failed for {ticker}, trying Alpha Vantage fallback...")
            detail = await self._get_detail_alpha_vantage(ticker)
            
        if not detail:
            # Last resort: try to at least get the live price if metadata is missing
            price_data = await self.get_live_price(ticker)
            if price_data.get("price", 0) > 0:
                return StockDetail(
                    ticker=ticker,
                    name=ticker, # Unknown name
                    exchange="",
                    current_price=price_data["price"],
                    price_change=price_data.get("change", 0),
                    price_change_pct=price_data.get("change_pct", 0),
                    volume=price_data.get("volume", 0),
                )
            return None
            
        # Ensure price is accurate from the best available source
        if detail.current_price == 0:
            price_data = await self.get_live_price(ticker)
            if price_data.get("price", 0) > 0:
                detail.current_price = price_data["price"]
                detail.price_change = price_data.get("change", 0)
                detail.price_change_pct = price_data.get("change_pct", 0)
                
        return detail

    async def _get_detail_yfinance(self, ticker: str) -> Optional[StockDetail]:
        try:
            # yfinance info is blocking, run in thread
            def _fetch():
                t = yf.Ticker(ticker)
                return t.info
            
            info = await asyncio.to_thread(_fetch)
            if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
                return None

            current = info.get("regularMarketPrice") or info.get("currentPrice", 0)
            prev_close = info.get("regularMarketPreviousClose", current)
            change = current - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0

            return StockDetail(
                ticker=ticker,
                name=info.get("longName") or info.get("shortName", ticker),
                exchange=info.get("exchange", ""),
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap"),
                pe_ratio=info.get("trailingPE"),
                eps=info.get("trailingEps"),
                dividend_yield=info.get("dividendYield"),
                week_52_high=info.get("fiftyTwoWeekHigh"),
                week_52_low=info.get("fiftyTwoWeekLow"),
                current_price=current,
                price_change=change,
                price_change_pct=change_pct,
                volume=info.get("regularMarketVolume", 0),
                avg_volume=info.get("averageVolume"),
            )
        except Exception as e:
            logger.warning(f"yfinance detail fetch failed for {ticker}: {e}")
            return None

    async def _get_detail_alpha_vantage(self, ticker: str) -> Optional[StockDetail]:
        # Alpha Vantage uses different suffixes or none. 
        # For Indian stocks, they often use .BSE or .NSE (note the dot)
        base_ticker = ticker.replace(".NS", "").replace(".BO", "")
        
        # We'll try the base ticker, and if that fails, we'll try common suffixes
        symbols_to_try = [base_ticker]
        if ".NS" in ticker: symbols_to_try.insert(0, f"{base_ticker}.NSE")
        if ".BO" in ticker: symbols_to_try.insert(0, f"{base_ticker}.BSE")
        
        for symbol in symbols_to_try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "OVERVIEW",
                "symbol": symbol,
                "apikey": settings.ALPHA_VANTAGE_API_KEY
            }
            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
                    resp = await client.get(url, params=params)
                    data = resp.json()
                
                if not data or "Symbol" not in data or data.get("Note"):
                    continue # Try next symbol if rate limited or not found
                    
                return StockDetail(
                    ticker=ticker,
                    name=data.get("Name", ticker),
                    exchange=data.get("Exchange", ""),
                    sector=data.get("Sector"),
                    industry=data.get("Industry"),
                    market_cap=float(data.get("MarketCapitalization", 0)) if data.get("MarketCapitalization") and data.get("MarketCapitalization") != "None" else None,
                    pe_ratio=float(data.get("PERatio", 0)) if data.get("PERatio") and data.get("PERatio") != "None" else None,
                    eps=float(data.get("EPS", 0)) if data.get("EPS") and data.get("EPS") != "None" else None,
                    dividend_yield=float(data.get("DividendYield", 0)) if data.get("DividendYield") and data.get("DividendYield") != "None" else None,
                    week_52_high=float(data.get("52WeekHigh", 0)) if data.get("52WeekHigh") and data.get("52WeekHigh") != "None" else None,
                    week_52_low=float(data.get("52WeekLow", 0)) if data.get("52WeekLow") and data.get("52WeekLow") != "None" else None,
                    current_price=0,
                    price_change=0,
                    price_change_pct=0,
                    volume=0,
                )
            except Exception as e:
                logger.warning(f"Alpha Vantage detail error for {symbol}: {e}")
                continue
        return None

    async def get_ohlcv(self, ticker: str, period: str = "1y", interval: str = "1d") -> List[OHLCVData]:
        """Fetch historical data. Primary: yfinance, Fallback: Alpha Vantage."""
        try:
            def _fetch():
                t = yf.Ticker(ticker)
                return t.history(period=period, interval=interval)
            
            hist = await asyncio.to_thread(_fetch)
            result = []
            for idx, row in hist.iterrows():
                result.append(OHLCVData(
                    date=idx.date(),
                    open=round(row["Open"], 4),
                    high=round(row["High"], 4),
                    low=round(row["Low"], 4),
                    close=round(row["Close"], 4),
                    volume=int(row["Volume"]),
                    adjusted_close=None,
                ))
            return result
        except Exception as e:
            logger.error(f"yfinance OHLCV error for {ticker}: {e}")
            # Alpha Vantage fallback could be added here for historical
            return []

    async def get_live_price(self, ticker: str) -> dict:
        """
        Fast multi-provider live price fetcher with competitive parallel racing.
        We launch multiple requests and take the first successful one.
        """
        providers = []
        
        # 1. Finnhub (very fast, reliable)
        if settings.FINNHUB_API_KEY:
            providers.append(self._get_price_finnhub(ticker))
            
        # 2. FMP (extremely fast, good for both US and global)
        if settings.FMP_API_KEY:
            providers.append(self._get_price_fmp(ticker))

        # 3. Alpha Vantage (reliable but slower, strict rate limits)
        if settings.ALPHA_VANTAGE_API_KEY:
            providers.append(self._get_price_alpha_vantage(ticker))
            
        # 3. yfinance (fallback, no key needed but can be slow/404)
        providers.append(self._get_price_yfinance(ticker))
        
        # Racing: return the first one that succeeds
        for task in asyncio.as_completed(providers):
            try:
                result = await task
                if result and result.get("price", 0) > 0:
                    return result
            except Exception:
                continue
        
        return {"ticker": ticker, "price": 0, "change": 0, "change_pct": 0, "volume": 0}

    async def _get_price_finnhub(self, ticker: str) -> dict:
        # Finnhub uses symbols like RELIANCE.NS
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={settings.FINNHUB_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=self.fast_timeout, verify=self.verify_ssl) as client:
                resp = await client.get(url)
                data = resp.json()
            
            if not data or not data.get("c"):
                return {}
                
            return {
                "ticker": ticker,
                "price": float(data["c"]),
                "change": float(data["d"]),
                "change_pct": float(data["dp"]),
                "volume": 0, # Finnhub quote doesn't always have volume
                "source": "finnhub"
            }
        except Exception:
            return {}

    async def _get_price_fmp(self, ticker: str) -> dict:
        """Fetch live price from Financial Modeling Prep."""
        # FMP sometimes uses different formats for Indian stocks, but often ticker.NS works
        url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={settings.FMP_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=self.fast_timeout, verify=self.verify_ssl) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
            
            if not data or not isinstance(data, list) or len(data) == 0:
                return {}
            
            quote = data[0]
            return {
                "ticker": ticker,
                "price": float(quote.get("price", 0)),
                "change": float(quote.get("change", 0)),
                "change_pct": float(quote.get("changesPercentage", 0)),
                "volume": int(quote.get("volume", 0)),
                "source": "fmp"
            }
        except Exception as e:
            logger.debug(f"FMP price fetch error for {ticker}: {e}")
            return {}

    async def _get_price_alpha_vantage(self, ticker: str) -> dict:
        base_ticker = ticker.replace(".NS", "").replace(".BO", "")
        symbols_to_try = [base_ticker]
        if ".NS" in ticker: symbols_to_try.insert(0, f"{base_ticker}.NSE")
        if ".BO" in ticker: symbols_to_try.insert(0, f"{base_ticker}.BSE")

        for symbol in symbols_to_try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": settings.ALPHA_VANTAGE_API_KEY
            }
            try:
                async with httpx.AsyncClient(timeout=self.fast_timeout, verify=self.verify_ssl) as client:
                    resp = await client.get(url, params=params)
                    data = resp.json()
                
                quote = data.get("Global Quote", {})
                if not quote or "05. price" not in quote:
                    continue
                    
                price = float(quote["05. price"])
                change = float(quote["09. change"])
                change_pct = float(quote["10. change percent"].strip("%"))
                
                return {
                    "ticker": ticker,
                    "price": price,
                    "change": change,
                    "change_pct": change_pct,
                    "volume": int(quote.get("06. volume", 0)),
                    "source": f"alphavantage:{symbol}"
                }
            except Exception:
                continue
        return {}

    async def _get_price_yfinance(self, ticker: str) -> dict:
        try:
            def _fetch():
                t = yf.Ticker(ticker)
                # fast_info is better for just prices
                return {
                    "price": t.fast_info.last_price,
                    "prev_close": t.fast_info.previous_close,
                    "volume": t.fast_info.last_volume
                }
            
            data = await asyncio.to_thread(_fetch)
            price = data["price"]
            prev_close = data["prev_close"]
            change = price - prev_close
            pct = (change / prev_close * 100) if prev_close else 0
            
            return {
                "ticker": ticker,
                "price": price,
                "change": round(change, 4),
                "change_pct": round(pct, 4),
                "volume": data["volume"],
                "source": "yfinance"
            }
        except Exception:
            return {}
