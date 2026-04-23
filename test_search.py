import asyncio
from app.services.data.stock_fetcher import StockDataFetcher

async def main():
    fetcher = StockDataFetcher()
    res = await fetcher.search_stocks("RELIANCE")
    for r in res:
        print(r)

asyncio.run(main())
