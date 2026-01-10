import pytest
import os
from unittest.mock import MagicMock, patch
from riskfusion.execution.alpaca_connector import AlpacaConnector

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
