"""
Circuit breaker pattern implementation for external API calls
Provides fault tolerance and graceful degradation
"""

import time
import asyncio
from typing import Dict, Any, Callable, Optional
from enum import Enum
import threading

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back

class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()
    
    def _can_attempt_reset(self) -> bool:
        """Check if we can attempt to reset the circuit"""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        with self.lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._can_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            return self.state != CircuitState.OPEN
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if not self._should_attempt_reset():
            raise Exception(f"Circuit breaker is OPEN. Service unavailable.")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
        except Exception as e:
            self._on_failure()
            raise e
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        with self.lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "last_failure_time": self.last_failure_time,
                "can_attempt_reset": self._can_attempt_reset() if self.last_failure_time else True
            }

class CircuitBreakerManager:
    """Manages multiple circuit breakers for different services"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.Lock()
    
    def get_breaker(self, service_name: str, **kwargs) -> CircuitBreaker:
        """Get or create circuit breaker for a service"""
        with self.lock:
            if service_name not in self.breakers:
                self.breakers[service_name] = CircuitBreaker(**kwargs)
            return self.breakers[service_name]
    
    async def call_with_breaker(self, 
                               service_name: str, 
                               func: Callable, 
                               *args, 
                               **kwargs) -> Any:
        """Call function with circuit breaker protection"""
        breaker = self.get_breaker(service_name)
        return await breaker.call(func, *args, **kwargs)
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        return {name: breaker.get_state() for name, breaker in self.breakers.items()}
    
    def reset_breaker(self, service_name: str) -> bool:
        """Reset a specific circuit breaker"""
        with self.lock:
            if service_name in self.breakers:
                breaker = self.breakers[service_name]
                breaker.failure_count = 0
                breaker.last_failure_time = None
                breaker.state = CircuitState.CLOSED
                return True
            return False

# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()

# Pre-configured circuit breakers for common services
def get_ton_api_breaker() -> CircuitBreaker:
    """Get circuit breaker for TON API calls"""
    return circuit_manager.get_breaker(
        "ton_api",
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=Exception
    )

def get_database_breaker() -> CircuitBreaker:
    """Get circuit breaker for database operations"""
    return circuit_manager.get_breaker(
        "database",
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=Exception
    )

def get_payment_breaker() -> CircuitBreaker:
    """Get circuit breaker for payment operations"""
    return circuit_manager.get_breaker(
        "payment",
        failure_threshold=3,
        recovery_timeout=120,
        expected_exception=Exception
    )

# Decorator for automatic circuit breaker protection
def with_circuit_breaker(service_name: str, **breaker_kwargs):
    """Decorator to add circuit breaker protection to functions"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            breaker = circuit_manager.get_breaker(service_name, **breaker_kwargs)
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
