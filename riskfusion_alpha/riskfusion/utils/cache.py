import os
import pickle
import hashlib
from pathlib import Path
from functools import wraps
import time
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("cache")

class FileCache:
    def __init__(self, cache_dir=None, ttl_seconds=86400):
        if cache_dir is None:
            config = get_config()
            cache_dir = Path(config.params['paths']['raw']) / "cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds

    def _get_path(self, key):
        hashed = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{hashed}.pkl"

    def get(self, key):
        path = self._get_path(key)
        if path.exists():
            try:
                # Check TTL
                if time.time() - path.stat().st_mtime > self.ttl:
                    return None
                
                with open(path, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
        return None

    def set(self, key, value):
        path = self._get_path(key)
        try:
            with open(path, "wb") as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

def cached(ttl=86400):
    """Decorator to cache function results to disk."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a key based on function name + args
            # Simple str representation (caveat: args order matters)
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            cache = FileCache(ttl_seconds=ttl)
            cached_val = cache.get(key)
            if cached_val is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_val
            
            val = func(*args, **kwargs)
            cache.set(key, val)
            return val
        return wrapper
    return decorator
