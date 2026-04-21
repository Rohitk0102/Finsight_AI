import httpx
from app.core.config import settings
from datetime import datetime


UPSTOX_BASE = "https://api.upstox.com/v2"


class UpstoxBroker:

    def get_auth_url(self) -> str:
        return (
            f"https://api.upstox.com/v2/login/authorization/dialog"
            f"?response_type=code"
            f"&client_id={settings.UPSTOX_CLIENT_ID}"
            f"&redirect_uri={settings.UPSTOX_REDIRECT_URI}"
        )

    async def exchange_code_for_token(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{UPSTOX_BASE}/login/authorization/token",
                data={
                    "code": code,
                    "client_id": settings.UPSTOX_CLIENT_ID,
                    "client_secret": settings.UPSTOX_CLIENT_SECRET,
                    "redirect_uri": settings.UPSTOX_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def get_profile(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{UPSTOX_BASE}/user/profile",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.json().get("data", {})

    async def fetch_holdings(self, api_key: str = None, access_token: str = None) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{UPSTOX_BASE}/portfolio/long-term-holdings",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            resp.raise_for_status()
            raw = resp.json().get("data", [])

        holdings = []
        for h in raw:
            qty = h.get("quantity", 0)
            avg = h.get("average_price", 0)
            ltp = h.get("last_price", 0)
            invested = qty * avg
            current = qty * ltp
            holdings.append({
                "ticker": h.get("isin", h["tradingsymbol"]),
                "name": h.get("company_name", h["tradingsymbol"]),
                "quantity": qty,
                "average_price": avg,
                "current_price": ltp,
                "current_value": current,
                "invested_value": invested,
                "unrealized_pnl": current - invested,
                "unrealized_pnl_pct": ((current - invested) / invested * 100) if invested else 0,
                "day_change": h.get("day_change", 0),
                "day_change_pct": h.get("day_change_percentage", 0),
                "last_updated": datetime.utcnow().isoformat(),
            })
        return holdings
