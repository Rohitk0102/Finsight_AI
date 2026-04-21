"""
Example usage of Groww Trading API Integration

Official Groww Trading API integration examples.
API Documentation: https://groww.in/trade-api/docs

Requirements:
- Active Groww Trading API subscription (₹499/month)
- Valid access token from Groww dashboard
"""

import asyncio
from app.services.broker.groww_broker import (
    GrowwBroker,
    GrowwAuthError,
    GrowwAPIConnectionError,
    GrowwDataError,
)


async def example_fetch_portfolio():
    """Example: Fetch complete portfolio data from Groww Trading API"""
    
    # Initialize broker
    broker = GrowwBroker()
    
    # Your Groww Trading API access token
    # Get this from: https://groww.in/trade-api (after subscribing)
    access_token = "your_groww_trading_api_token_here"
    
    try:
        # Validate token first (optional but recommended)
        print("Validating token...")
        is_valid = await broker.validate_token(access_token)
        if not is_valid:
            print("❌ Invalid access token. Please check your subscription.")
            return
        
        print("✅ Token valid\n")
        
        # Fetch complete portfolio
        print("Fetching portfolio...")
        portfolio = await broker.get_complete_portfolio(
            access_token=access_token,
            include_positions=True
        )
        
        # Display summary
        summary = portfolio['summary']
        print("\n" + "="*50)
        print("PORTFOLIO SUMMARY")
        print("="*50)
        print(f"Total Invested:    ₹{summary['total_invested']:>12,.2f}")
        print(f"Current Value:     ₹{summary['total_current_value']:>12,.2f}")
        print(f"Unrealized P&L:    ₹{summary['total_unrealized_pnl']:>12,.2f}")
        print(f"P&L Percentage:     {summary['total_unrealized_pnl_pct']:>11.2f}%")
        print(f"Day Change:        ₹{summary['day_change']:>12,.2f}")
        print(f"Day Change %:       {summary['day_change_pct']:>11.2f}%")
        print(f"Holdings Count:     {summary['holdings_count']:>12}")
        print(f"Positions Count:    {summary['positions_count']:>12}")
        print("="*50)
        
        # Display individual holdings
        if portfolio['holdings']:
            print("\n" + "="*50)
            print("HOLDINGS")
            print("="*50)
            for holding in portfolio['holdings']:
                pnl_symbol = "📈" if holding['unrealized_pnl'] >= 0 else "📉"
                print(f"\n{pnl_symbol} {holding['name']} ({holding['ticker']})")
                print(f"   Quantity:       {holding['quantity']:>10.2f}")
                print(f"   Avg Price:      ₹{holding['average_price']:>10.2f}")
                print(f"   Current Price:  ₹{holding['current_price']:>10.2f}")
                print(f"   Invested:       ₹{holding['invested_value']:>10,.2f}")
                print(f"   Current Value:  ₹{holding['current_value']:>10,.2f}")
                print(f"   P&L:            ₹{holding['unrealized_pnl']:>10,.2f} ({holding['unrealized_pnl_pct']:>6.2f}%)")
        
        # Display positions
        if portfolio['positions']:
            print("\n" + "="*50)
            print("POSITIONS")
            print("="*50)
            for position in portfolio['positions']:
                pnl_symbol = "📈" if position['pnl'] >= 0 else "📉"
                print(f"\n{pnl_symbol} {position['name']} ({position['ticker']})")
                print(f"   Quantity:       {position['quantity']:>10.2f}")
                print(f"   Buy Price:      ₹{position['buy_price']:>10.2f}")
                print(f"   Current Price:  ₹{position['current_price']:>10.2f}")
                print(f"   P&L:            ₹{position['pnl']:>10,.2f} ({position['pnl_pct']:>6.2f}%)")
        
    except GrowwAuthError as e:
        print(f"❌ Authentication error: {e}")
        print("\nPlease check:")
        print("1. Your Groww Trading API subscription is active")
        print("2. Access token is correct")
        print("3. Visit: https://groww.in/trade-api")
    except GrowwAPIConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("\nPlease check your internet connection and try again.")
    except GrowwDataError as e:
        print(f"❌ Data error: {e}")
    finally:
        await broker.close()


async def example_fetch_holdings_only():
    """Example: Fetch only holdings (no positions)"""
    
    broker = GrowwBroker()
    access_token = "your_groww_trading_api_token_here"
    
    try:
        print("Fetching holdings...")
        holdings = await broker.fetch_holdings(access_token=access_token)
        
        print(f"\nFound {len(holdings)} holdings:\n")
        for h in holdings:
            print(f"• {h['name']:<30} ₹{h['current_value']:>12,.2f}")
            
    except GrowwAuthError as e:
        print(f"❌ Auth error: {e}")
    finally:
        await broker.close()


async def example_calculate_summary():
    """Example: Calculate portfolio summary from holdings"""
    
    broker = GrowwBroker()
    access_token = "your_groww_trading_api_token_here"
    
    try:
        holdings = await broker.fetch_holdings(access_token=access_token)
        summary = broker.calculate_portfolio_summary(holdings)
        
        print("Portfolio Summary:")
        print(f"  Total Invested:    ₹{summary['total_invested']:,.2f}")
        print(f"  Current Value:     ₹{summary['total_current_value']:,.2f}")
        print(f"  Unrealized P&L:    ₹{summary['total_unrealized_pnl']:,.2f}")
        print(f"  P&L Percentage:     {summary['total_unrealized_pnl_pct']:.2f}%")
        print(f"  Day Change:        ₹{summary['day_change']:,.2f}")
        print(f"  Day Change %:       {summary['day_change_pct']:.2f}%")
        
    finally:
        await broker.close()


def example_csv_import():
    """Example: Import portfolio from CSV (fallback method)"""
    
    broker = GrowwBroker()
    
    # Sample CSV content (export from Groww app)
    csv_content = """Symbol,Quantity,Avg Cost,LTP
RELIANCE,10,2500.00,2847.50
TCS,5,3200.00,3450.00
INFY,15,1400.00,1520.00
HDFCBANK,8,1600.00,1612.00"""
    
    print("Importing from CSV...")
    holdings = broker.import_from_csv(csv_content)
    
    print(f"\nImported {len(holdings)} holdings:\n")
    for h in holdings:
        pnl_symbol = "📈" if h['unrealized_pnl_pct'] >= 0 else "📉"
        print(f"{pnl_symbol} {h['name']:<15} ₹{h['current_value']:>10,.2f} (P&L: {h['unrealized_pnl_pct']:>6.2f}%)")


# FastAPI Integration Example
async def fastapi_endpoint_example():
    """
    Example FastAPI endpoint integration
    
    Add this to your FastAPI routes file:
    """
    from fastapi import APIRouter, HTTPException, Depends
    from app.core.dependencies import get_current_user
    
    router = APIRouter(prefix="/api/v1/broker/groww", tags=["broker"])
    
    @router.get("/portfolio")
    async def get_groww_portfolio(current_user = Depends(get_current_user)):
        """
        Fetch Groww portfolio for current user
        
        Requires:
        - Active Groww Trading API subscription
        - Valid access token stored in database
        """
        
        # Get user's stored access token from database
        # This should be encrypted in production
        # access_token = await get_user_broker_token(current_user.id, "groww")
        access_token = "user_token_from_db"
        
        if not access_token:
            raise HTTPException(
                status_code=400, 
                detail="Groww API token not configured. Please link your account."
            )
        
        broker = GrowwBroker()
        
        try:
            portfolio = await broker.get_complete_portfolio(access_token)
            return {
                "success": True,
                "data": portfolio
            }
            
        except GrowwAuthError:
            raise HTTPException(
                status_code=401, 
                detail="Invalid Groww token. Please renew your API subscription."
            )
        except GrowwAPIConnectionError:
            raise HTTPException(
                status_code=503, 
                detail="Groww API unavailable. Please try again later."
            )
        except GrowwDataError:
            raise HTTPException(
                status_code=500, 
                detail="Failed to process portfolio data."
            )
        finally:
            await broker.close()
    
    @router.get("/holdings")
    async def get_groww_holdings(current_user = Depends(get_current_user)):
        """Fetch only holdings (no positions)"""
        
        access_token = "user_token_from_db"
        broker = GrowwBroker()
        
        try:
            holdings = await broker.fetch_holdings(access_token=access_token)
            return {
                "success": True,
                "holdings": holdings,
                "count": len(holdings)
            }
        except GrowwAuthError:
            raise HTTPException(status_code=401, detail="Invalid token")
        finally:
            await broker.close()
    
    @router.post("/sync")
    async def sync_groww_portfolio(current_user = Depends(get_current_user)):
        """
        Sync Groww portfolio to database
        
        This endpoint fetches portfolio from Groww and stores it in your database
        """
        access_token = "user_token_from_db"
        broker = GrowwBroker()
        
        try:
            portfolio = await broker.get_complete_portfolio(access_token)
            
            # Store in database
            # await save_portfolio_to_db(current_user.id, portfolio)
            
            return {
                "success": True,
                "message": "Portfolio synced successfully",
                "holdings_count": len(portfolio['holdings']),
                "last_synced": portfolio['summary']['last_updated']
            }
        except GrowwAuthError:
            raise HTTPException(status_code=401, detail="Invalid token")
        finally:
            await broker.close()


def print_setup_instructions():
    """Print setup instructions for Groww Trading API"""
    print("\n" + "="*60)
    print("GROWW TRADING API SETUP")
    print("="*60)
    print("\n1. Subscribe to Groww Trading API:")
    print("   → Visit: https://groww.in/trade-api")
    print("   → Cost: ₹499 + taxes per month")
    print("\n2. Get your access token:")
    print("   → Login to Groww")
    print("   → Go to API dashboard")
    print("   → Copy your access token")
    print("\n3. Update the examples:")
    print("   → Replace 'your_groww_trading_api_token_here' with your token")
    print("\n4. Run the examples:")
    print("   → python -m backend.app.services.broker.groww_example")
    print("\n" + "="*60)
    print("\nAPI Documentation: https://groww.in/trade-api/docs")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Print setup instructions
    print_setup_instructions()
    
    # Run examples
    print("\n📊 Example 1: Fetch Complete Portfolio")
    print("-" * 60)
    asyncio.run(example_fetch_portfolio())
    
    print("\n\n📋 Example 2: CSV Import (Fallback)")
    print("-" * 60)
    example_csv_import()
