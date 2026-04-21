from app.core.config import settings
from datetime import datetime


class ZerodhaBroker:
    """
    Zerodha Kite Connect integration.
    Requires: kiteconnect package (pip install kiteconnect)
    """

    def get_auth_url(self) -> str:
        return f"https://kite.zerodha.com/connect/login?v=3&api_key={settings.ZERODHA_API_KEY}"

    async def generate_session(self, request_token: str) -> dict:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=settings.ZERODHA_API_KEY)
        session = kite.generate_session(request_token, api_secret=settings.ZERODHA_API_SECRET)
        return session

    async def get_profile(self, access_token: str) -> dict:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=settings.ZERODHA_API_KEY)
        kite.set_access_token(access_token)
        return kite.profile()

    async def fetch_holdings(self, api_key: str = None, access_token: str = None) -> list[dict]:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key or settings.ZERODHA_API_KEY)
        kite.set_access_token(access_token)
        raw = kite.holdings()

        holdings = []
        for h in raw:
            invested = h["average_price"] * h["quantity"]
            current = h["last_price"] * h["quantity"]
            holdings.append({
                "ticker": h["tradingsymbol"] + ".NS",
                "name": h["tradingsymbol"],
                "quantity": h["quantity"],
                "average_price": h["average_price"],
                "current_price": h["last_price"],
                "current_value": current,
                "invested_value": invested,
                "unrealized_pnl": current - invested,
                "unrealized_pnl_pct": ((current - invested) / invested * 100) if invested else 0,
                "day_change": h.get("day_change", 0),
                "day_change_pct": h.get("day_change_percentage", 0),
                "last_updated": datetime.utcnow().isoformat(),
            })
        return holdings
