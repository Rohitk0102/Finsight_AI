"""
Unit tests for Groww Trading API Integration
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from app.services.broker.groww_broker import (
    GrowwBroker,
    GrowwAuthError,
    GrowwAPIConnectionError,
    GrowwDataError,
)


@pytest.fixture
def groww_broker():
    """Create GrowwBroker instance"""
    return GrowwBroker()


@pytest.fixture
def sample_holdings_response():
    """Sample API response for holdings"""
    return {
        "holdings": [
            {
                "symbol": "RELIANCE",
                "companyName": "Reliance Industries Ltd",
                "quantity": 10,
                "avgPrice": 2500.00,
                "ltp": 2847.50,
                "dayChange": 25.50,
                "dayChangePct": 0.90,
            },
            {
                "symbol": "TCS",
                "companyName": "Tata Consultancy Services",
                "quantity": 5,
                "avgPrice": 3200.00,
                "ltp": 3450.00,
                "dayChange": 15.00,
                "dayChangePct": 0.44,
            },
        ]
    }


@pytest.fixture
def sample_positions_response():
    """Sample API response for positions"""
    return {
        "positions": [
            {
                "symbol": "INFY",
                "companyName": "Infosys Ltd",
                "quantity": 20,
                "buyPrice": 1400.00,
                "ltp": 1520.00,
                "type": "LONG",
            }
        ]
    }


class TestGrowwBrokerInit:
    """Test broker initialization"""
    
    def test_init(self, groww_broker):
        """Test broker initializes correctly"""
        assert groww_broker._client is None
        assert groww_broker.BASE_URL == "https://api.groww.in"
        assert groww_broker.TIMEOUT == 30.0


class TestAuthentication:
    """Test authentication methods"""
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self, groww_broker):
        """Test successful token validation"""
        with patch.object(groww_broker, '_get_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_client.return_value = mock_http_client
            
            result = await groww_broker.validate_token("valid_token")
            
            assert result is True
            mock_http_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, groww_broker):
        """Test invalid token validation"""
        with patch.object(groww_broker, '_get_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_client.return_value = mock_http_client
            
            result = await groww_broker.validate_token("invalid_token")
            
            assert result is False
    
    def test_get_auth_headers(self, groww_broker):
        """Test authentication headers generation"""
        headers = groww_broker._get_auth_headers("test_token")
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["X-Platform"] == "web"


class TestFetchHoldings:
    """Test holdings fetching"""
    
    @pytest.mark.asyncio
    async def test_fetch_holdings_success(self, groww_broker, sample_holdings_response):
        """Test successful holdings fetch"""
        with patch.object(groww_broker, '_get_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_holdings_response
            
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_client.return_value = mock_http_client
            
            holdings = await groww_broker.fetch_holdings(access_token="valid_token")
            
            assert len(holdings) == 2
            assert holdings[0]["ticker"] == "RELIANCE.NS"
            assert holdings[0]["quantity"] == 10
            assert holdings[0]["average_price"] == 2500.00
            assert holdings[0]["current_price"] == 2847.50
            assert holdings[0]["invested_value"] == 25000.00
            assert holdings[0]["current_value"] == 28475.00
            assert holdings[0]["unrealized_pnl"] == 3475.00
    
    @pytest.mark.asyncio
    async def test_fetch_holdings_no_token(self, groww_broker):
        """Test holdings fetch without token"""
        with pytest.raises(GrowwAuthError, match="Access token is required"):
            await groww_broker.fetch_holdings()
    
    @pytest.mark.asyncio
    async def test_fetch_holdings_invalid_token(self, groww_broker):
        """Test holdings fetch with invalid token"""
        with patch.object(groww_broker, '_get_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_client.return_value = mock_http_client
            
            with pytest.raises(GrowwAuthError, match="Invalid or expired"):
                await groww_broker.fetch_holdings(access_token="invalid_token")
    
    @pytest.mark.asyncio
    async def test_fetch_holdings_api_error(self, groww_broker):
        """Test holdings fetch with API error"""
        with patch.object(groww_broker, '_get_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_client.return_value = mock_http_client
            
            with pytest.raises(GrowwAPIConnectionError):
                await groww_broker.fetch_holdings(access_token="valid_token")
    
    @pytest.mark.asyncio
    async def test_fetch_holdings_empty_data(self, groww_broker):
        """Test holdings fetch with empty data"""
        with patch.object(groww_broker, '_get_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"holdings": []}
            
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_client.return_value = mock_http_client
            
            holdings = await groww_broker.fetch_holdings(access_token="valid_token")
            
            assert holdings == []


class TestFetchPositions:
    """Test positions fetching"""
    
    @pytest.mark.asyncio
    async def test_fetch_positions_success(self, groww_broker, sample_positions_response):
        """Test successful positions fetch"""
        with patch.object(groww_broker, '_get_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_positions_response
            
            mock_http_client = AsyncMock()
            mock_http_client.get.return_value = mock_response
            mock_client.return_value = mock_http_client
            
            positions = await groww_broker.fetch_positions("valid_token")
            
            assert len(positions) == 1
            assert positions[0]["ticker"] == "INFY.NS"
            assert positions[0]["quantity"] == 20
            assert positions[0]["buy_price"] == 1400.00
            assert positions[0]["current_price"] == 1520.00


class TestPortfolioSummary:
    """Test portfolio summary calculation"""
    
    def test_calculate_summary_basic(self, groww_broker):
        """Test basic summary calculation"""
        holdings = [
            {
                "invested_value": 25000.00,
                "current_value": 28475.00,
                "quantity": 10,
                "day_change": 25.50,
            },
            {
                "invested_value": 16000.00,
                "current_value": 17250.00,
                "quantity": 5,
                "day_change": 15.00,
            },
        ]
        
        summary = groww_broker.calculate_portfolio_summary(holdings)
        
        assert summary["total_invested"] == 41000.00
        assert summary["total_current_value"] == 45725.00
        assert summary["total_unrealized_pnl"] == 4725.00
        assert summary["holdings_count"] == 2
    
    def test_calculate_summary_with_positions(self, groww_broker):
        """Test summary with positions included"""
        holdings = [
            {
                "invested_value": 25000.00,
                "current_value": 28475.00,
                "quantity": 10,
                "day_change": 25.50,
            },
        ]
        
        positions = [
            {
                "invested_value": 28000.00,
                "current_value": 30400.00,
            },
        ]
        
        summary = groww_broker.calculate_portfolio_summary(holdings, positions)
        
        assert summary["total_invested"] == 53000.00
        assert summary["total_current_value"] == 58875.00
        assert summary["positions_count"] == 1
    
    def test_calculate_summary_empty(self, groww_broker):
        """Test summary with empty holdings"""
        summary = groww_broker.calculate_portfolio_summary([])
        
        assert summary["total_invested"] == 0
        assert summary["total_current_value"] == 0
        assert summary["holdings_count"] == 0


class TestCompletePortfolio:
    """Test complete portfolio fetching"""
    
    @pytest.mark.asyncio
    async def test_get_complete_portfolio(
        self, 
        groww_broker, 
        sample_holdings_response,
        sample_positions_response
    ):
        """Test fetching complete portfolio"""
        with patch.object(groww_broker, '_get_client') as mock_client:
            mock_http_client = AsyncMock()
            
            # Mock holdings response
            holdings_response = Mock()
            holdings_response.status_code = 200
            holdings_response.json.return_value = sample_holdings_response
            
            # Mock positions response
            positions_response = Mock()
            positions_response.status_code = 200
            positions_response.json.return_value = sample_positions_response
            
            mock_http_client.get.side_effect = [holdings_response, positions_response]
            mock_client.return_value = mock_http_client
            
            portfolio = await groww_broker.get_complete_portfolio("valid_token")
            
            assert "holdings" in portfolio
            assert "positions" in portfolio
            assert "summary" in portfolio
            assert len(portfolio["holdings"]) == 2
            assert len(portfolio["positions"]) == 1


class TestCSVImport:
    """Test CSV import functionality"""
    
    def test_import_csv_success(self, groww_broker):
        """Test successful CSV import"""
        csv_content = """Symbol,Quantity,Avg Cost,LTP
RELIANCE,10,2500.00,2847.50
TCS,5,3200.00,3450.00"""
        
        holdings = groww_broker.import_from_csv(csv_content)
        
        assert len(holdings) == 2
        assert holdings[0]["ticker"] == "RELIANCE.NS"
        assert holdings[0]["quantity"] == 10
        assert holdings[1]["ticker"] == "TCS.NS"
    
    def test_import_csv_invalid_data(self, groww_broker):
        """Test CSV import with invalid data"""
        csv_content = """Symbol,Quantity,Avg Cost,LTP
RELIANCE,invalid,2500.00,2847.50
TCS,5,3200.00,3450.00"""
        
        holdings = groww_broker.import_from_csv(csv_content)
        
        # Should skip invalid row
        assert len(holdings) == 1
        assert holdings[0]["ticker"] == "TCS.NS"
    
    def test_import_csv_empty(self, groww_broker):
        """Test CSV import with empty content"""
        csv_content = """Symbol,Quantity,Avg Cost,LTP"""
        
        holdings = groww_broker.import_from_csv(csv_content)
        
        assert holdings == []


class TestUtilityMethods:
    """Test utility methods"""
    
    def test_safe_decimal_valid(self, groww_broker):
        """Test safe decimal conversion with valid input"""
        result = groww_broker._safe_decimal("123.45")
        assert float(result) == 123.45
    
    def test_safe_decimal_invalid(self, groww_broker):
        """Test safe decimal conversion with invalid input"""
        result = groww_broker._safe_decimal("invalid")
        assert float(result) == 0
    
    def test_safe_decimal_none(self, groww_broker):
        """Test safe decimal conversion with None"""
        result = groww_broker._safe_decimal(None)
        assert float(result) == 0
    
    def test_get_auth_url_not_implemented(self, groww_broker):
        """Test that get_auth_url raises NotImplementedError"""
        with pytest.raises(NotImplementedError):
            groww_broker.get_auth_url()
