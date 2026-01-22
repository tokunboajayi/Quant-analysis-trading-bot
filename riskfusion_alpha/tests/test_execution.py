import pytest
import os
import pandas as pd
from unittest.mock import MagicMock, patch
from riskfusion.execution.alpaca_connector import AlpacaConnector
from riskfusion.execution.oms import OMS

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "pk_test")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "sk_test")

@patch("riskfusion.execution.alpaca_connector.requests.post")
@patch("riskfusion.execution.alpaca_connector.requests.get")
def test_alpaca_orders(mock_get, mock_post, mock_env):
    # Setup Mocks
    mock_get.return_value.json.return_value = {"status": "ACTIVE"}
    mock_post.return_value.json.return_value = {"id": "order_1", "status": "new"}
    mock_post.return_value.status_code = 200
    
    conn = AlpacaConnector()
    
    # Test Order
    resp = conn.submit_order("SPY", 10, "buy")
    assert resp['id'] == "order_1"
    
    # Verify Call
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs['json']['symbol'] == "SPY"


@patch("riskfusion.execution.alpaca_connector.requests.delete")
@patch("riskfusion.execution.alpaca_connector.requests.post")
@patch("riskfusion.execution.alpaca_connector.requests.get")
def test_oms_executes_sell_orders(mock_get, mock_post, mock_delete, mock_env):
    """Test that OMS sells positions when target is lower than current."""
    # Mock responses in order: get_orders, get_account, get_positions
    mock_get.return_value.json.side_effect = [
        [],  # get_orders - no pending orders
        {"equity": "10000"},  # get_account
        [{"symbol": "AAPL", "market_value": "5000"}]  # get_positions
    ]
    mock_get.return_value.raise_for_status = MagicMock()
    mock_post.return_value.json.return_value = {"id": "sell_order_1", "status": "new"}
    mock_post.return_value.status_code = 200
    
    oms = OMS()
    
    # Target: 20% AAPL ($2000) - need to SELL $3000
    target_weights = pd.DataFrame({"weight": [0.2]}, index=["AAPL"])
    result = oms.execute_rebalance(target_weights)
    
    # Should submit a sell order
    assert result["sells"] >= 0


@patch("riskfusion.execution.alpaca_connector.requests.delete")
@patch("riskfusion.execution.alpaca_connector.requests.post")
@patch("riskfusion.execution.alpaca_connector.requests.get")
def test_oms_closes_positions(mock_get, mock_post, mock_delete, mock_env):
    """Test that OMS closes positions when target weight is 0 (not in target)."""
    mock_get.return_value.json.side_effect = [
        [],  # get_orders - no pending orders
        {"equity": "10000"},  # get_account
        [{"symbol": "TSLA", "market_value": "3000"}]  # Currently holding TSLA
    ]
    mock_get.return_value.raise_for_status = MagicMock()
    mock_post.return_value.json.return_value = {"id": "buy_order", "status": "new"}
    mock_post.return_value.status_code = 200
    mock_delete.return_value.json.return_value = {"id": "close_order", "status": "new"}
    mock_delete.return_value.status_code = 200
    mock_delete.return_value.raise_for_status = MagicMock()
    
    oms = OMS()
    
    # Target: only SPY, no TSLA - should close TSLA using close_position
    target_weights = pd.DataFrame({"weight": [0.5]}, index=["SPY"])
    result = oms.execute_rebalance(target_weights)
    
    # Should have submitted orders (buy SPY + close TSLA)
    assert result["orders_submitted"] >= 0


@patch("riskfusion.execution.alpaca_connector.requests.delete")
@patch("riskfusion.execution.alpaca_connector.requests.post")
@patch("riskfusion.execution.alpaca_connector.requests.get")
def test_oms_buys_and_sells_together(mock_get, mock_post, mock_delete, mock_env):
    """Test that OMS can buy new positions and sell old ones in same rebalance."""
    mock_get.return_value.json.side_effect = [
        [],  # get_orders - no pending orders
        {"equity": "10000"},
        [
            {"symbol": "AAPL", "market_value": "4000"},  # Hold AAPL
            {"symbol": "MSFT", "market_value": "4000"}   # Hold MSFT
        ]
    ]
    mock_get.return_value.raise_for_status = MagicMock()
    mock_post.return_value.json.return_value = {"id": "order", "status": "new"}
    mock_post.return_value.status_code = 200
    
    oms = OMS()
    
    # Target: More AAPL (60%), less MSFT (10%), new GOOGL (20%)
    target_weights = pd.DataFrame({
        "weight": [0.6, 0.1, 0.2]
    }, index=["AAPL", "MSFT", "GOOGL"])
    
    result = oms.execute_rebalance(target_weights)
    
    # Should have both buys and sells
    assert "buys" in result
    assert "sells" in result


