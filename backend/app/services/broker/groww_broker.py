"""
Groww Trading API Integration Module

Official Groww Trading API integration for portfolio management.
API Documentation: https://groww.in/trade-api/docs

Features:
- Fetch holdings from DEMAT account
- Fetch trading positions
- Calculate portfolio summary with P&L
- Secure Bearer token authentication
- Comprehensive error handling
- Production-ready logging

Pricing: ₹499 + taxes per month
Eligibility: Available to all Groww account holders

API Endpoints:
- Holdings: GET /v1/holdings/user
- Positions: GET /v1/positions/user
"""

import csv
import io
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from decimal import Decimal, InvalidOperation


logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GrowwAPIError(Exception):
    """Base exception for Groww API errors"""
    pass


class GrowwAuthError(GrowwAPIError):
    """Raised when authentication fails"""
    pass


class GrowwAPIConnectionError(GrowwAPIError):
    """Raised when API connection fails"""
    pass


class GrowwDataError(GrowwAPIError):
    """Raised when data parsing fails"""
    pass


class GrowwBroker:
    """
    Groww Trading API Integration
    
    Official API integration for fetching portfolio data from Groww.
    Requires a valid access token from Groww Trading API subscription.
    
    API Documentation: https://groww.in/trade-api/docs
    """
    
    # Official Groww API endpoints
    BASE_URL = "https://api.groww.in"
    HOLDINGS_ENDPOINT = "/v1/holdings/user"
    POSITIONS_ENDPOINT = "/v1/positions/user"
    
    # Request timeout in seconds
    TIMEOUT = 30.0
    
    def __init__(self):
        """Initialize Groww broker with default configuration"""
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper configuration"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.TIMEOUT),
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; FinsightAI/1.0)",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
            )
        return self._client
    
    async def close(self):
        """Close HTTP client connection"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def _get_auth_headers(self, access_token: str) -> Dict[str, str]:
        """
        Generate authentication headers for Groww API requests
        
        Args:
            access_token: User's Groww Trading API access token
            
        Returns:
            Dictionary of headers with Bearer token authorization
        """
        return {
            "Authorization": f"Bearer {access_token}",
            "X-Platform": "web",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    async def validate_token(self, access_token: str) -> bool:
        """
        Validate if the Groww Trading API access token is valid
        
        Args:
            access_token: User's Groww Trading API access token
            
        Returns:
            True if token is valid, False otherwise
            
        Raises:
            GrowwAPIConnectionError: If API connection fails
        """
        try:
            client = await self._get_client()
            headers = self._get_auth_headers(access_token)
            
            # Try to fetch holdings to validate token
            response = await client.get(
                f"{self.BASE_URL}{self.HOLDINGS_ENDPOINT}",
                headers=headers
            )
            
            return response.status_code == 200
            
        except httpx.RequestError as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise GrowwAPIConnectionError(f"Failed to connect to Groww API: {str(e)}")
    
    async def fetch_holdings(
        self, 
        api_key: str = None, 
        access_token: str = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch user's stock holdings from DEMAT account via Groww Trading API
        
        Endpoint: GET /v1/holdings/user
        Documentation: https://groww.in/trade-api/docs/curl/portfolio
        
        Args:
            api_key: Not used for Groww (kept for interface compatibility)
            access_token: User's Groww Trading API access token (required)
            
        Returns:
            List of holdings with detailed P&L information
            
        Raises:
            GrowwAuthError: If access token is invalid or expired
            GrowwAPIConnectionError: If API connection fails
            GrowwDataError: If response data is invalid
        """
        if not access_token:
            raise GrowwAuthError("Access token is required")
        
        try:
            client = await self._get_client()
            headers = self._get_auth_headers(access_token)
            
            logger.info("Fetching holdings from Groww Trading API")
            response = await client.get(
                f"{self.BASE_URL}{self.HOLDINGS_ENDPOINT}",
                headers=headers
            )
            
            if response.status_code == 401:
                raise GrowwAuthError(
                    "Invalid or expired access token. "
                    "Please renew your Groww Trading API subscription."
                )
            
            if response.status_code == 403:
                raise GrowwAuthError(
                    "Access forbidden. Ensure your Groww Trading API subscription is active."
                )
            
            if response.status_code == 429:
                raise GrowwAPIConnectionError(
                    "Rate limit exceeded. Please try again later."
                )
            
            if response.status_code != 200:
                raise GrowwAPIConnectionError(
                    f"API returned status {response.status_code}: {response.text}"
                )
            
            data = response.json()
            
            # Handle different response structures
            if isinstance(data, dict):
                holdings_data = data.get("data", data.get("holdings", []))
            elif isinstance(data, list):
                holdings_data = data
            else:
                raise GrowwDataError("Unexpected response format")
            
            if not isinstance(holdings_data, list):
                raise GrowwDataError("Invalid holdings data format")
            
            logger.info(f"Successfully fetched {len(holdings_data)} holdings")
            return self._process_holdings(holdings_data)
            
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch holdings: {str(e)}")
            raise GrowwAPIConnectionError(f"Failed to connect to Groww API: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse holdings data: {str(e)}")
            raise GrowwDataError(f"Invalid response format: {str(e)}")
    
    async def fetch_positions(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Fetch user's trading positions via Groww Trading API
        
        Endpoint: GET /v1/positions/user
        Documentation: https://groww.in/trade-api/docs/curl/portfolio
        
        Args:
            access_token: User's Groww Trading API access token
            
        Returns:
            List of positions with P&L information
            
        Raises:
            GrowwAuthError: If access token is invalid
            GrowwAPIConnectionError: If API connection fails
            GrowwDataError: If response data is invalid
        """
        if not access_token:
            raise GrowwAuthError("Access token is required")
        
        try:
            client = await self._get_client()
            headers = self._get_auth_headers(access_token)
            
            logger.info("Fetching positions from Groww Trading API")
            response = await client.get(
                f"{self.BASE_URL}{self.POSITIONS_ENDPOINT}",
                headers=headers
            )
            
            if response.status_code == 401:
                raise GrowwAuthError("Invalid or expired access token")
            
            if response.status_code == 429:
                raise GrowwAPIConnectionError("Rate limit exceeded")
            
            if response.status_code != 200:
                raise GrowwAPIConnectionError(
                    f"API returned status {response.status_code}: {response.text}"
                )
            
            data = response.json()
            
            # Handle different response structures
            if isinstance(data, dict):
                positions_data = data.get("data", data.get("positions", []))
            elif isinstance(data, list):
                positions_data = data
            else:
                positions_data = []
            
            logger.info(f"Successfully fetched {len(positions_data)} positions")
            return self._process_positions(positions_data)
            
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch positions: {str(e)}")
            raise GrowwAPIConnectionError(f"Failed to connect to Groww API: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse positions data: {str(e)}")
            raise GrowwDataError(f"Invalid response format: {str(e)}")
    
    def _process_holdings(self, raw_holdings: List[Dict]) -> List[Dict[str, Any]]:
        """
        Process raw holdings data from Groww API into standardized format
        
        Args:
            raw_holdings: Raw holdings data from Groww Trading API
            
        Returns:
            Processed holdings list with calculated P&L
        """
        holdings = []
        
        for item in raw_holdings:
            try:
                # Handle different field names from Groww API
                ticker = (
                    item.get("symbol") or 
                    item.get("tradingSymbol") or 
                    item.get("stockSymbol") or 
                    ""
                ).strip()
                
                if not ticker:
                    continue
                
                # Extract quantity and prices
                quantity = self._safe_decimal(
                    item.get("quantity") or 
                    item.get("qty") or 
                    0
                )
                
                avg_price = self._safe_decimal(
                    item.get("avgPrice") or 
                    item.get("averagePrice") or 
                    item.get("buyAvgPrice") or 
                    0
                )
                
                current_price = self._safe_decimal(
                    item.get("ltp") or 
                    item.get("lastPrice") or 
                    item.get("currentPrice") or 
                    0
                )
                
                # Calculate values
                invested_value = quantity * avg_price
                current_value = quantity * current_price
                unrealized_pnl = current_value - invested_value
                unrealized_pnl_pct = (
                    (unrealized_pnl / invested_value * 100) 
                    if invested_value > 0 else 0
                )
                
                # Day change
                day_change = self._safe_decimal(
                    item.get("dayChange") or 
                    item.get("change") or 
                    0
                )
                day_change_pct = self._safe_decimal(
                    item.get("dayChangePct") or 
                    item.get("changePct") or 
                    item.get("pnlPercentage") or 
                    0
                )
                
                holdings.append({
                    "ticker": f"{ticker}.NS" if not ticker.endswith(".NS") else ticker,
                    "name": item.get("companyName") or item.get("name") or ticker,
                    "quantity": float(quantity),
                    "average_price": float(avg_price),
                    "current_price": float(current_price),
                    "current_value": float(current_value),
                    "invested_value": float(invested_value),
                    "unrealized_pnl": float(unrealized_pnl),
                    "unrealized_pnl_pct": float(unrealized_pnl_pct),
                    "day_change": float(day_change),
                    "day_change_pct": float(day_change_pct),
                    "last_updated": _utc_now_iso(),
                })
                
            except (ValueError, InvalidOperation, TypeError) as e:
                logger.warning(f"Skipping invalid holding: {str(e)}")
                continue
        
        return holdings
    
    def _process_positions(self, raw_positions: List[Dict]) -> List[Dict[str, Any]]:
        """
        Process raw positions data into standardized format
        
        Args:
            raw_positions: Raw positions data from API
            
        Returns:
            Processed positions list
        """
        positions = []
        
        for item in raw_positions:
            try:
                ticker = item.get("symbol", "").strip()
                if not ticker:
                    continue
                
                quantity = self._safe_decimal(item.get("quantity", 0))
                buy_price = self._safe_decimal(item.get("buyPrice", 0))
                current_price = self._safe_decimal(item.get("ltp", 0))
                
                invested = quantity * buy_price
                current = quantity * current_price
                pnl = current - invested
                pnl_pct = (pnl / invested * 100) if invested > 0 else 0
                
                positions.append({
                    "ticker": f"{ticker}.NS",
                    "name": item.get("companyName", ticker),
                    "quantity": float(quantity),
                    "buy_price": float(buy_price),
                    "current_price": float(current_price),
                    "invested_value": float(invested),
                    "current_value": float(current),
                    "pnl": float(pnl),
                    "pnl_pct": float(pnl_pct),
                    "position_type": item.get("type", "LONG"),
                    "last_updated": _utc_now_iso(),
                })
                
            except (ValueError, InvalidOperation, TypeError) as e:
                logger.warning(f"Skipping invalid position: {str(e)}")
                continue
        
        return positions
    
    def _safe_decimal(self, value: Any) -> Decimal:
        """
        Safely convert value to Decimal
        
        Args:
            value: Value to convert
            
        Returns:
            Decimal value or 0 if conversion fails
        """
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")
    
    def calculate_portfolio_summary(
        self, 
        holdings: List[Dict[str, Any]],
        positions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive portfolio summary
        
        Args:
            holdings: List of holdings
            positions: Optional list of positions
            
        Returns:
            Portfolio summary with totals and metrics
        """
        total_invested = sum(h["invested_value"] for h in holdings)
        total_current = sum(h["current_value"] for h in holdings)
        total_pnl = total_current - total_invested
        total_pnl_pct = (
            (total_pnl / total_invested * 100) 
            if total_invested > 0 else 0
        )
        
        total_day_change = sum(
            h["quantity"] * h["day_change"] 
            for h in holdings
        )
        total_day_change_pct = (
            (total_day_change / total_current * 100) 
            if total_current > 0 else 0
        )
        
        # Include positions if provided
        if positions:
            pos_invested = sum(p["invested_value"] for p in positions)
            pos_current = sum(p["current_value"] for p in positions)
            total_invested += pos_invested
            total_current += pos_current
            total_pnl = total_current - total_invested
            total_pnl_pct = (
                (total_pnl / total_invested * 100) 
                if total_invested > 0 else 0
            )
        
        return {
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_current, 2),
            "total_unrealized_pnl": round(total_pnl, 2),
            "total_unrealized_pnl_pct": round(total_pnl_pct, 2),
            "day_change": round(total_day_change, 2),
            "day_change_pct": round(total_day_change_pct, 2),
            "holdings_count": len(holdings),
            "positions_count": len(positions) if positions else 0,
            "last_updated": _utc_now_iso(),
        }
    
    async def get_complete_portfolio(
        self, 
        access_token: str,
        include_positions: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch complete portfolio data with summary
        
        Args:
            access_token: User's Groww access token
            include_positions: Whether to include positions data
            
        Returns:
            Complete portfolio data with holdings, positions, and summary
            
        Raises:
            GrowwAuthError: If access token is invalid
            GrowwAPIConnectionError: If API connection fails
        """
        holdings = await self.fetch_holdings(access_token=access_token)
        
        positions = []
        if include_positions:
            try:
                positions = await self.fetch_positions(access_token)
            except GrowwAPIError as e:
                logger.warning(f"Failed to fetch positions: {str(e)}")
        
        summary = self.calculate_portfolio_summary(holdings, positions)
        
        return {
            "holdings": holdings,
            "positions": positions,
            "summary": summary,
        }
    
    # ===== CSV Import Fallback =====
    
    def import_from_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse Groww portfolio CSV export (fallback method)
        
        Expected columns: Symbol, Quantity, Avg Cost, LTP
        
        Args:
            csv_content: CSV file content as string
            
        Returns:
            List of holdings parsed from CSV
        """
        holdings = []
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in reader:
            try:
                ticker = row.get("Symbol", "").strip()
                if not ticker:
                    continue
                
                qty = float(row.get("Quantity", 0))
                avg = float(row.get("Avg Cost", 0))
                ltp = float(row.get("LTP", 0))
                
                invested = qty * avg
                current = qty * ltp
                
                holdings.append({
                    "ticker": f"{ticker}.NS",
                    "name": ticker,
                    "quantity": qty,
                    "average_price": avg,
                    "current_price": ltp,
                    "current_value": current,
                    "invested_value": invested,
                    "unrealized_pnl": current - invested,
                    "unrealized_pnl_pct": (
                        ((current - invested) / invested * 100) 
                        if invested else 0
                    ),
                    "day_change": 0,
                    "day_change_pct": 0,
                    "last_updated": _utc_now_iso(),
                })
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid CSV row: {str(e)}")
                continue
        
        return holdings
    
    def get_auth_url(self) -> str:
        """
        Get Groww Trading API subscription URL
        
        Returns:
            URL to subscribe to Groww Trading API
        """
        raise NotImplementedError("Groww Trading API uses manual access tokens and does not support an OAuth auth URL")
    
    def get_api_docs_url(self) -> str:
        """
        Get Groww Trading API documentation URL
        
        Returns:
            URL to API documentation
        """
        return "https://groww.in/trade-api/docs"
