import os
import requests
import json
from typing import List, Dict, Optional
from riskfusion.utils.logging import get_logger

logger = get_logger("alpaca_connector")

class AlpacaConnector:
    def __init__(self):
        self.api_key = os.environ.get("ALPACA_API_KEY")
        self.secret_key = os.environ.get("ALPACA_SECRET_KEY")
        self.base_url = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not self.api_key or not self.secret_key:
            logger.warning("Alpaca credentials not found. Execution will fail.")
            
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }

    def get_account(self) -> Dict:
        """Get account details."""
        resp = requests.get(f"{self.base_url}/v2/account", headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_positions(self) -> List[Dict]:
        """Get open positions."""
        resp = requests.get(f"{self.base_url}/v2/positions", headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def submit_order(self, symbol: str, qty: float = None, notional: float = None, side: str = "buy", type: str = "market", time_in_force: str = "day") -> Dict:
        """
        Submit an order.    
        side: 'buy' or 'sell'
        qty: number of shares (can be fractional if enabled)
        notional: dollar amount (alternative to qty)
        """
        payload = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "time_in_force": time_in_force
        }
        
        if notional is not None:
            payload["notional"] = notional
        elif qty is not None:
            payload["qty"] = qty
        else:
            raise ValueError("Must specify either qty or notional")
        
        logger.info(f"Submitting Order: {side} {notional or qty} {symbol}")
        resp = requests.post(f"{self.base_url}/v2/orders", headers=self.headers, json=payload)
        
        if resp.status_code != 200:
            logger.error(f"Order failed: {resp.text}")
            resp.raise_for_status()
            
        return resp.json()

    def close_all_positions(self):
        """Liquidate all positions."""
        logger.warning("Closing ALL positions.")
        resp = requests.delete(f"{self.base_url}/v2/positions", headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def close_position(self, symbol: str) -> Dict:
        """Close a single position completely."""
        logger.info(f"Closing position: {symbol}")
        resp = requests.delete(f"{self.base_url}/v2/positions/{symbol}", headers=self.headers)
        if resp.status_code != 200:
            logger.error(f"Close position failed: {resp.text}")
            resp.raise_for_status()
        return resp.json()

    def cancel_all_orders(self) -> List[Dict]:
        """Cancel all open orders."""
        logger.warning("Cancelling ALL open orders.")
        resp = requests.delete(f"{self.base_url}/v2/orders", headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_orders(self, status: str = "open") -> List[Dict]:
        """Get orders by status (open, closed, all)."""
        resp = requests.get(f"{self.base_url}/v2/orders?status={status}", headers=self.headers)
        resp.raise_for_status()
        return resp.json()
