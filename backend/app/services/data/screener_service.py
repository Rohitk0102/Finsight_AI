import asyncio
from typing import List, Dict, Optional, Any
from app.core.supabase import supabase
from app.services.data.stock_fetcher import StockDataFetcher
from loguru import logger

class ScreenerService:
    def __init__(self):
        self.fetcher = StockDataFetcher()

    async def get_metadata(self) -> Dict[str, List[str]]:
        """Fetch unique sectors and exchanges for frontend filters."""
        try:
            # We fetch unique sectors and exchanges
            # Using select with distinct equivalent in Supabase/PostgREST
            sector_res = await asyncio.to_thread(
                lambda: supabase.table("stocks").select("sector").not_.is_("sector", "null").execute()
            )
            exchange_res = await asyncio.to_thread(
                lambda: supabase.table("stocks").select("exchange").not_.is_("exchange", "null").execute()
            )
            
            # Extract unique values
            sectors = sorted(list(set(s["sector"] for s in sector_res.data if s.get("sector"))))
            exchanges = sorted(list(set(e["exchange"] for e in exchange_res.data if e.get("exchange"))))
            
            return {
                "sectors": sectors,
                "exchanges": exchanges
            }
        except Exception as e:
            logger.error(f"Failed to fetch screener metadata: {e}")
            return {"sectors": [], "exchanges": []}

    async def scan_stocks(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan stocks in the database using fundamental filters,
        then augment with live price data.
        """
        try:
            # 1. Build Query
            # We explicitly select columns to avoid serialization issues with hidden columns like 'updated_at'
            # and to minimize data transfer.
            columns = "ticker,name,exchange,sector,market_cap,pe_ratio,eps,isin"
            query = supabase.table("stocks").select(columns)
            
            if filters.get("exchange"):
                query = query.eq("exchange", filters["exchange"])
            
            if filters.get("sector"):
                # Use ILIKE for case-insensitive matching and handle Healthcare variations
                sector_val = filters["sector"]
                if sector_val.lower().replace(" ", "") == "healthcare":
                    query = query.or_("sector.ilike.Healthcare,sector.ilike.Health Care")
                else:
                    query = query.ilike("sector", sector_val)
                
            if filters.get("min_market_cap"):
                query = query.gte("market_cap", filters["min_market_cap"])
                
            if filters.get("max_pe"):
                query = query.lte("pe_ratio", filters["max_pe"])
            
            # Apply limit
            limit = filters.get("limit", 20)
            query = query.limit(limit)
            
            # 2. Execute Database Query
            try:
                res = await asyncio.to_thread(query.execute)
                stocks = res.data or []
            except Exception as db_exc:
                err_msg = str(db_exc)
                if "1101" in err_msg or "Cloudflare" in err_msg or "JSON could not be generated" in err_msg:
                    logger.error(f"Supabase serialization error (Cloudflare 1101): {err_msg}")
                    # Fallback or meaningful error
                    return [] 
                raise db_exc
            
            if not stocks:
                return []

            # 3. Augment with Live Prices
            # We concurrently fetch live prices for all matching stocks
            tasks = [self.fetcher.get_live_price(s["ticker"]) for s in stocks]
            live_prices = await asyncio.gather(*tasks)
            
            # 4. Merge Results
            final_results = []
            for i, stock in enumerate(stocks):
                live_data = live_prices[i]
                
                # Combine database metadata with live price data
                # We prioritize live data for price and change
                result = {
                    "ticker": stock["ticker"],
                    "name": stock["name"],
                    "exchange": stock["exchange"],
                    "sector": stock["sector"],
                    "market_cap": stock["market_cap"],
                    "pe_ratio": stock["pe_ratio"],
                    "current_price": live_data.get("price", 0),
                    "price_change": live_data.get("change", 0),
                    "price_change_pct": live_data.get("change_pct", 0),
                }
                final_results.append(result)
                
            return final_results

        except Exception as e:
            logger.error(f"Screener scan failed: {e}")
            raise e
