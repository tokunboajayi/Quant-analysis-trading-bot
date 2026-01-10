import time
import functools
import random
from typing import Type, Tuple, Callable
from riskfusion.utils.logging import get_logger

logger = get_logger("retry")

def retry(
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.1
):
    """
    Retry decorator with exponential backoff and jitter.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    msg = f"{str(e)}, Retrying in {mdelay:.2f} seconds..."
                    logger.warning(msg)
                    
                    # Sleep with jitter
                    sleep_time = mdelay + random.uniform(-jitter, jitter)
                    time.sleep(max(0, sleep_time))
                    
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    """
    Simple Circuit Breaker.
    If 'failure_threshold' failures happen in a row, open circuit for 'recovery_timeout' seconds.
    """
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit Breaker HALF_OPEN: Trying request...")
            else:
                raise CircuitBreakerOpenException("Circuit Breaker is OPEN. Request blocked.")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
                logger.info("Circuit Breaker CLOSED: Recovery successful.")
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit Breaker OPENED after {self.failures} failures.")
            raise e
