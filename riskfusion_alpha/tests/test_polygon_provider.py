import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from riskfusion.providers.prices_polygon import PolygonPriceProvider

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("POLYGON_API_KEY", "test_key")

@patch("riskfusion.providers.prices_polygon.requests.get")
def test_polygon_download(mock_get, mock_env):
    # Setup Mock Response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"o": 100, "h": 105, "l": 95, "c": 102, "v": 1000, "t": 1609459200000}, # 2021-01-01
            {"o": 102, "h": 108, "l": 101, "c": 107, "v": 1200, "t": 1609545600000}  # 2021-01-02
        ]
    }
    mock_get.return_value = mock_resp
    
    provider = PolygonPriceProvider()
    df = provider.download_prices(["AAPL"], "2021-01-01", "2021-01-05")
    
    assert not df.empty
    assert len(df) == 2
    assert "Open" in df.columns
    assert "Date" in df.columns
    assert df.iloc[0]["Close"] == 102
