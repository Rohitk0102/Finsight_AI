# Groww Trading API Integration

Official integration module for Groww Trading API to fetch portfolio data.

## Overview

This module provides a production-ready integration with Groww's official Trading API, allowing you to fetch real-time portfolio data including holdings and positions from user DEMAT accounts.

## Official API Information

- **API Documentation**: https://groww.in/trade-api/docs
- **Pricing**: ₹499 + taxes per month
- **Eligibility**: Available to all Groww account holders
- **Python SDK**: Available (optional)

## Features

✅ Fetch stock holdings from DEMAT account  
✅ Fetch trading positions (intraday)  
✅ Calculate comprehensive portfolio summary  
✅ Secure Bearer token authentication  
✅ Comprehensive error handling  
✅ Production-ready logging  
✅ CSV import fallback  
✅ Rate limit handling  
✅ Async/await support

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/holdings/user` | GET | Fetch current stock holdings |
| `/v1/positions/user` | GET | Fetch trading positions |

## Installation

No additional dependencies required beyond the base project requirements:

```bash
# Already included in requirements.txt
httpx
pydantic
```

## Quick Start

### 1. Get Access Token

Subscribe to Groww Trading API:
1. Visit https://groww.in/trade-api
2. Subscribe for ₹499/month
3. Get your access token from the dashboard

### 2. Basic Usage

```python
from app.services.broker.groww_broker import GrowwBroker

# Initialize broker
broker = GrowwBroker()

# Your Groww Trading API access token
access_token = "your_groww_api_token"

# Fetch complete portfolio
portfolio = await broker.get_complete_portfolio(access_token)

print(f"Total Invested: ₹{portfolio['summary']['total_invested']:,.2f}")
print(f"Current Value: ₹{portfolio['summary']['total_current_value']:,.2f}")
print(f"P&L: ₹{portfolio['summary']['total_unrealized_pnl']:,.2f}")
```

## API Methods

### Core Methods

#### `fetch_holdings(access_token: str) -> List[Dict]`

Fetch stock holdings from DEMAT account.

```python
holdings = await broker.fetch_holdings(access_token="your_token")

for holding in holdings:
    print(f"{holding['name']}: ₹{holding['current_value']:,.2f}")
```

**Returns:**
```python
[
    {
        "ticker": "RELIANCE.NS",
        "name": "Reliance Industries Ltd",
        "quantity": 10.0,
        "average_price": 2500.00,
        "current_price": 2847.50,
        "current_value": 28475.00,
        "invested_value": 25000.00,
        "unrealized_pnl": 3475.00,
        "unrealized_pnl_pct": 13.90,
        "day_change": 25.50,
        "day_change_pct": 0.90,
        "last_updated": "2024-01-15T10:30:00"
    }
]
```

#### `fetch_positions(access_token: str) -> List[Dict]`

Fetch trading positions (intraday trades).

```python
positions = await broker.fetch_positions(access_token="your_token")
```

#### `get_complete_portfolio(access_token: str) -> Dict`

Fetch complete portfolio with summary.

```python
portfolio = await broker.get_complete_portfolio(
    access_token="your_token",
    include_positions=True
)

# Access data
holdings = portfolio['holdings']
positions = portfolio['positions']
summary = portfolio['summary']
```

**Returns:**
```python
{
    "holdings": [...],
    "positions": [...],
    "summary": {
        "total_invested": 41000.00,
        "total_current_value": 45725.00,
        "total_unrealized_pnl": 4725.00,
        "total_unrealized_pnl_pct": 11.52,
        "day_change": 330.00,
        "day_change_pct": 0.72,
        "holdings_count": 5,
        "positions_count": 2,
        "last_updated": "2024-01-15T10:30:00"
    }
}
```

#### `calculate_portfolio_summary(holdings, positions) -> Dict`

Calculate portfolio summary from holdings and positions.

```python
summary = broker.calculate_portfolio_summary(holdings, positions)
```

### Utility Methods

#### `validate_token(access_token: str) -> bool`

Validate if access token is valid.

```python
is_valid = await broker.validate_token("your_token")
if not is_valid:
    print("Token expired or invalid")
```

#### `import_from_csv(csv_content: str) -> List[Dict]`

Import portfolio from CSV (fallback method).

```python
csv_content = """Symbol,Quantity,Avg Cost,LTP
RELIANCE,10,2500.00,2847.50
TCS,5,3200.00,3450.00"""

holdings = broker.import_from_csv(csv_content)
```

## Error Handling

The module provides specific exceptions for different error scenarios:

```python
from app.services.broker.groww_broker import (
    GrowwAuthError,
    GrowwAPIConnectionError,
    GrowwDataError,
)

try:
    portfolio = await broker.get_complete_portfolio(access_token)
except GrowwAuthError as e:
    # Invalid or expired token
    print(f"Authentication failed: {e}")
except GrowwAPIConnectionError as e:
    # Network or API connection issues
    print(f"Connection error: {e}")
except GrowwDataError as e:
    # Invalid response data
    print(f"Data parsing error: {e}")
```

### Exception Types

| Exception | Description | HTTP Status |
|-----------|-------------|-------------|
| `GrowwAuthError` | Invalid/expired token | 401, 403 |
| `GrowwAPIConnectionError` | Network/API errors | 500, 503, 429 |
| `GrowwDataError` | Invalid response format | - |

## FastAPI Integration

```python
from fastapi import APIRouter, HTTPException, Depends
from app.services.broker.groww_broker import GrowwBroker, GrowwAuthError

router = APIRouter(prefix="/api/v1/broker/groww", tags=["broker"])

@router.get("/portfolio")
async def get_portfolio(current_user = Depends(get_current_user)):
    """Fetch Groww portfolio"""
    
    # Get user's stored token from database
    access_token = await get_user_broker_token(current_user.id, "groww")
    
    broker = GrowwBroker()
    
    try:
        portfolio = await broker.get_complete_portfolio(access_token)
        return portfolio
    except GrowwAuthError:
        raise HTTPException(status_code=401, detail="Invalid Groww token")
    finally:
        await broker.close()
```

## Security Best Practices

### 1. Token Storage

Store access tokens securely in your database:

```python
from cryptography.fernet import Fernet

# Encrypt token before storing
def encrypt_token(token: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(token.encode()).decode()

# Decrypt when using
def decrypt_token(encrypted_token: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted_token.encode()).decode()
```

### 2. Token Validation

Always validate tokens before use:

```python
if not await broker.validate_token(access_token):
    # Prompt user to renew subscription
    raise HTTPException(status_code=401, detail="Token expired")
```

### 3. Rate Limiting

Implement rate limiting to avoid API throttling:

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.get("/portfolio")
@limiter.limit("10/minute")
async def get_portfolio():
    ...
```

## Testing

Run the test suite:

```bash
pytest backend/tests/test_groww_broker.py -v
```

## Example Application

See `groww_example.py` for complete usage examples including:
- Fetching portfolio data
- Error handling
- FastAPI integration
- CSV import

## Troubleshooting

### Token Invalid/Expired

**Error**: `GrowwAuthError: Invalid or expired access token`

**Solution**: 
1. Check if your Groww Trading API subscription is active
2. Renew subscription at https://groww.in/trade-api
3. Get a new access token

### Rate Limit Exceeded

**Error**: `GrowwAPIConnectionError: Rate limit exceeded`

**Solution**:
1. Implement exponential backoff
2. Cache portfolio data
3. Reduce API call frequency

### Empty Holdings

**Issue**: API returns empty holdings list

**Possible Causes**:
1. No stocks in DEMAT account
2. Token doesn't have portfolio access
3. API subscription inactive

## Groww MCP Integration

Groww also offers MCP (Model Context Protocol) integration for AI assistants:

- **Documentation**: https://groww.in/updates/groww-mcp
- **Use Case**: Connect Groww to Claude/Cursor for AI-powered portfolio analysis
- **Example Queries**: 
  - "Show me top performers from my stocks portfolio"
  - "Am I overexposed to mid-cap funds?"

## Support

- **API Documentation**: https://groww.in/trade-api/docs
- **Groww Support**: Contact via Groww app
- **Module Issues**: Create an issue in the project repository

## License

This integration module is part of the Finsight AI project.

## Changelog

### v1.0.0 (2024-01-15)
- Initial release with official Groww Trading API support
- Holdings and positions fetching
- Portfolio summary calculation
- Comprehensive error handling
- CSV import fallback
