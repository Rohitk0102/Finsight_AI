from app.core.config import settings
from datetime import datetime


class AngelOneBroker:

    async def login(self, client_id: str, mpin: str, totp: str) -> dict:
        from SmartApi import SmartConnect
        obj = SmartConnect(api_key=settings.ANGEL_ONE_API_KEY)
        data = obj.generateSession(client_id, mpin, totp)
        if data["status"] is False:
            raise ValueError(data.get("message", "Angel One login failed"))
        return data

    async def fetch_holdings(self, api_key: str = None, access_token: str = None) -> list[dict]:
        from SmartApi import SmartConnect
        obj = SmartConnect(api_key=api_key or settings.ANGEL_ONE_API_KEY)
        obj.setSessionExpiryHook(lambda: None)
        if access_token:
            obj.setAccessToken(access_token)
        raw = obj.holding()
        holdings = []
        for h in raw.get("data", []):
            qty = h.get("quantity", 0)
            avg = h.get("averageprice", 0)
            ltp = h.get("ltp", 0)
            invested = qty * avg
            current = qty * ltp
            holdings.append({
                "ticker": h.get("tradingsymbol", "") + ".NS",
                "name": h.get("symbolname", ""),
                "quantity": qty,
                "average_price": avg,
                "current_price": ltp,
                "current_value": current,
                "invested_value": invested,
                "unrealized_pnl": current - invested,
                "unrealized_pnl_pct": ((current - invested) / invested * 100) if invested else 0,
                "day_change": 0,
                "day_change_pct": 0,
                "last_updated": datetime.utcnow().isoformat(),
            })
        return holdings
