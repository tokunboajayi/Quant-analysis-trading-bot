import os
import yaml
from pathlib import Path
from typing import Any, Dict

class Config:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to configs/default.yaml relative to project root
            root_dir = Path(__file__).parent.parent
            config_path = root_dir / "configs" / "default.yaml"
        
        self.config_path = Path(config_path)
        self.params = self._load_config()
        self._setup_paths()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
        
        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)
        
        # Override with env vars if needed
        config["price_provider"] = os.environ.get("PRICE_PROVIDER", "yfinance")
        return config

    def _setup_paths(self):
        # Convert relative paths to absolute based on project root
        root_dir = self.config_path.parent.parent
        
        paths = self.params.get("paths", {})
        for key, path in paths.items():
            abs_path = root_dir / path
            self.params["paths"][key] = str(abs_path)
            os.makedirs(abs_path, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        val = self.params
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    @property
    def universe(self):
        return self.params.get("universe", {}).get("tickers", [])

# Global instance
_config_instance = None

def get_config(path=None):
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(path)
    return _config_instance
