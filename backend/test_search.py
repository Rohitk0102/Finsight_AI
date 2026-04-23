import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data.stock_fetcher import StockDataFetcher
from app.core.config import settings

settings.FINNHUB_API_KEY = None
settings.FMP_API_KEY = None

async def main():
    fetcher = StockDataFetcher()
    res = await fetcher.search_stocks("RELIANCE")
    for r in res:
        print(r)

asyncio.run(main())
