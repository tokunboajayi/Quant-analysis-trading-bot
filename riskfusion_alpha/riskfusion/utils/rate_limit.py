import time
import threading
from riskfusion.utils.logging import get_logger

logger = get_logger("rate_limit")

class RateLimiter:
    """
    Token Bucket Rate Limiter.
    Thread-safe.
    """
    def __init__(self, max_calls: int, period: float):
        """
        max_calls: Number of calls allowed per period
        period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.tokens = max_calls
        self.last_update = time.time()
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.time()
            # Replenish tokens
            elapsed = now - self.last_update
            new_tokens = elapsed * (self.max_calls / self.period)
            if new_tokens > 0:
                self.tokens = min(self.max_calls, self.tokens + new_tokens)
                self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            else:
                # Need to wait
                wait_time = (1 - self.tokens) * (self.period / self.max_calls)
                logger.debug(f"Rate limit hit. Waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                self.tokens = 0
                self.last_update = time.time()
