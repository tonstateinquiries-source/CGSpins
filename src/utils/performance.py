"""
Advanced performance monitoring and optimization for CG Spins Bot
Tracks detailed metrics and provides performance insights
"""

import time
import asyncio
import threading
import psutil
import gc
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta
from contextlib import asynccontextmanager, contextmanager
import functools

from .logger import get_logger

logger = get_logger("Performance")

class PerformanceTracker:
    """Advanced performance tracking with detailed metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_metrics = defaultdict(list)
        self.function_metrics = defaultdict(list)
        self.memory_snapshots = deque(maxlen=100)
        self.gc_stats = deque(maxlen=50)
        self.lock = threading.Lock()
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def _start_background_monitoring(self):
        """Start background monitoring tasks"""
        def monitor_memory():
            while True:
                try:
                    process = psutil.Process()
                    memory_info = {
                        "timestamp": time.time(),
                        "rss_mb": process.memory_info().rss / 1024 / 1024,
                        "vms_mb": process.memory_info().vms / 1024 / 1024,
                        "percent": process.memory_percent(),
                        "available_mb": psutil.virtual_memory().available / 1024 / 1024
                    }
                    
                    with self.lock:
                        self.memory_snapshots.append(memory_info)
                    
                    time.sleep(30)  # Monitor every 30 seconds
                except Exception as e:
                    logger.error(f"Memory monitoring error: {e}")
                    time.sleep(60)
        
        def monitor_gc():
            while True:
                try:
                    gc_stats = {
                        "timestamp": time.time(),
                        "collections": gc.get_count(),
                        "thresholds": gc.get_threshold()
                    }
                    
                    with self.lock:
                        self.gc_stats.append(gc_stats)
                    
                    time.sleep(60)  # Monitor every minute
                except Exception as e:
                    logger.error(f"GC monitoring error: {e}")
                    time.sleep(120)
        
        # Start monitoring threads
        threading.Thread(target=monitor_memory, daemon=True).start()
        threading.Thread(target=monitor_gc, daemon=True).start()
    
    def record_request(self, request_type: str, duration: float, success: bool = True):
        """Record request performance metrics"""
        with self.lock:
            self.request_metrics[request_type].append({
                "timestamp": time.time(),
                "duration": duration,
                "success": success
            })
            
            # Keep only last 1000 requests per type
            if len(self.request_metrics[request_type]) > 1000:
                self.request_metrics[request_type] = self.request_metrics[request_type][-1000:]
    
    def record_function(self, function_name: str, duration: float, success: bool = True):
        """Record function performance metrics"""
        with self.lock:
            self.function_metrics[function_name].append({
                "timestamp": time.time(),
                "duration": duration,
                "success": success
            })
            
            # Keep only last 500 calls per function
            if len(self.function_metrics[function_name]) > 500:
                self.function_metrics[function_name] = self.function_metrics[function_name][-500:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self.lock:
            uptime = time.time() - self.start_time
            
            # Calculate request metrics
            request_summary = {}
            for req_type, metrics in self.request_metrics.items():
                if metrics:
                    durations = [m["duration"] for m in metrics]
                    successes = [m["success"] for m in metrics]
                    
                    request_summary[req_type] = {
                        "total_requests": len(metrics),
                        "success_rate": sum(successes) / len(successes) * 100,
                        "avg_duration": sum(durations) / len(durations),
                        "min_duration": min(durations),
                        "max_duration": max(durations),
                        "p95_duration": sorted(durations)[int(len(durations) * 0.95)] if durations else 0
                    }
            
            # Calculate function metrics
            function_summary = {}
            for func_name, metrics in self.function_metrics.items():
                if metrics:
                    durations = [m["duration"] for m in metrics]
                    successes = [m["success"] for m in metrics]
                    
                    function_summary[func_name] = {
                        "total_calls": len(metrics),
                        "success_rate": sum(successes) / len(successes) * 100,
                        "avg_duration": sum(durations) / len(durations),
                        "min_duration": min(durations),
                        "max_duration": max(durations),
                        "p95_duration": sorted(durations)[int(len(durations) * 0.95)] if durations else 0
                    }
            
            # Memory metrics
            memory_summary = {}
            if self.memory_snapshots:
                latest_memory = self.memory_snapshots[-1]
                memory_summary = {
                    "current_rss_mb": latest_memory["rss_mb"],
                    "current_vms_mb": latest_memory["vms_mb"],
                    "current_percent": latest_memory["percent"],
                    "available_mb": latest_memory["available_mb"]
                }
                
                # Calculate memory trends
                if len(self.memory_snapshots) > 1:
                    memory_trend = []
                    for i in range(1, min(len(self.memory_snapshots), 10)):
                        prev = self.memory_snapshots[-i-1]["rss_mb"]
                        curr = self.memory_snapshots[-i]["rss_mb"]
                        memory_trend.append(curr - prev)
                    
                    memory_summary["memory_trend_mb"] = sum(memory_trend) / len(memory_trend)
            
            return {
                "uptime_seconds": uptime,
                "uptime_formatted": str(timedelta(seconds=int(uptime))),
                "request_metrics": request_summary,
                "function_metrics": function_summary,
                "memory_metrics": memory_summary,
                "gc_stats": list(self.gc_stats)[-5:] if self.gc_stats else []
            }

# Global performance tracker
performance_tracker = PerformanceTracker()

def track_performance(request_type: str = "unknown"):
    """Decorator to track function performance"""
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    raise e
                finally:
                    duration = time.time() - start_time
                    performance_tracker.record_function(func.__name__, duration, success)
                    performance_tracker.record_request(request_type, duration, success)
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    raise e
                finally:
                    duration = time.time() - start_time
                    performance_tracker.record_function(func.__name__, duration, success)
                    performance_tracker.record_request(request_type, duration, success)
            
            return sync_wrapper
    
    return decorator

@asynccontextmanager
async def track_async_operation(operation_name: str):
    """Context manager for tracking async operations"""
    start_time = time.time()
    success = True
    try:
        yield
    except Exception as e:
        success = False
        raise e
    finally:
        duration = time.time() - start_time
        performance_tracker.record_function(operation_name, duration, success)

@contextmanager
def track_sync_operation(operation_name: str):
    """Context manager for tracking sync operations"""
    start_time = time.time()
    success = True
    try:
        yield
    except Exception as e:
        success = False
        raise e
    finally:
        duration = time.time() - start_time
        performance_tracker.record_function(operation_name, duration, success)

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def optimize_memory():
        """Perform memory optimization"""
        # Force garbage collection
        collected = gc.collect()
        
        # Get memory stats
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024
        
        logger.info(f"Memory optimization: collected {collected} objects, current memory: {memory_before:.1f}MB")
        
        return {
            "objects_collected": collected,
            "memory_mb": memory_before
        }
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get detailed memory usage information"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "available_system_mb": psutil.virtual_memory().available / 1024 / 1024,
            "system_memory_percent": psutil.virtual_memory().percent
        }

class AsyncOptimizer:
    """Async operation optimization utilities"""
    
    @staticmethod
    async def batch_operations(operations: List[Callable], batch_size: int = 10):
        """Execute operations in batches for better performance"""
        results = []
        
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
        
        return results
    
    @staticmethod
    async def with_timeout(operation: Callable, timeout: float = 30.0):
        """Execute operation with timeout"""
        try:
            return await asyncio.wait_for(operation(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout} seconds")
            raise

# Global instances
memory_optimizer = MemoryOptimizer()
async_optimizer = AsyncOptimizer()
