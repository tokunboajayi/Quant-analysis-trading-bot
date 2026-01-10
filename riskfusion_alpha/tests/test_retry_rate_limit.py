import pytest
import time
from unittest.mock import Mock
from riskfusion.utils.retry import retry, CircuitBreaker, CircuitBreakerOpenException
from riskfusion.utils.rate_limit import RateLimiter

def test_retry_sucess():
    mock_func = Mock()
    mock_func.side_effect = [ValueError("Fail"), "Success"]
    
    @retry(tries=3, delay=0.01)
    def call_it():
        return mock_func()
        
    assert call_it() == "Success"
    assert mock_func.call_count == 2

def test_retry_fail():
    mock_func = Mock()
    mock_func.side_effect = ValueError("Fail")
    
    @retry(tries=2, delay=0.01)
    def call_it():
        return mock_func()
        
    with pytest.raises(ValueError):
        call_it()
    assert mock_func.call_count == 2

def test_circuit_breaker():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
    
    # Fail 1
    with pytest.raises(ValueError):
        cb.call(lambda: (_ for _ in ()).throw(ValueError("Fail")))
    assert cb.state == "CLOSED"
    
    # Fail 2 -> Open
    with pytest.raises(ValueError):
        cb.call(lambda: (_ for _ in ()).throw(ValueError("Fail")))
    assert cb.state == "OPEN"
    
    # Immediate call -> Short circuit
    with pytest.raises(CircuitBreakerOpenException):
        cb.call(lambda: "Should not run")
    
    # Wait recovery
    time.sleep(0.15)
    
    # Next call -> Half Open -> Success -> Closed
    res = cb.call(lambda: "Success")
    assert res == "Success"
    assert cb.state == "CLOSED"

def test_rate_limiter():
    # 2 calls per 0.1s
    rl = RateLimiter(max_calls=2, period=0.1)
    
    start = time.time()
    rl.wait()
    rl.wait()
    # Third should wait
    rl.wait()
    dur = time.time() - start
    assert dur >= 0.05 # rough check
