"""
Monitoring and health check system for CG Spins Bot
Tracks performance metrics, system health, and provides alerts
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

from .logger import get_logger

logger = get_logger("Monitoring")

class BotMetrics:
    """Tracks various bot performance metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.success_count = 0
        self.response_times = deque(maxlen=100)  # Keep last 100 response times
        self.error_types = defaultdict(int)
        self.user_activity = defaultdict(int)
        self.ton_api_calls = 0
        self.ton_api_errors = 0
        self.payment_attempts = 0
        self.payment_successes = 0
        
    def record_request(self, user_id: Optional[int] = None, request_type: str = "unknown"):
        """Record a new request"""
        self.request_count += 1
        if user_id:
            self.user_activity[user_id] += 1
    
    def record_success(self, response_time: float = 0.0):
        """Record a successful request"""
        self.success_count += 1
        if response_time > 0:
            self.response_times.append(response_time)
    
    def record_error(self, error_type: str, user_id: Optional[int] = None):
        """Record an error"""
        self.error_count += 1
        self.error_types[error_type] += 1
        if user_id:
            self.user_activity[user_id] += 1
    
    def record_ton_api_call(self, success: bool = True):
        """Record TON API call"""
        self.ton_api_calls += 1
        if not success:
            self.ton_api_errors += 1
    
    def record_payment_attempt(self, success: bool = True):
        """Record payment attempt"""
        self.payment_attempts += 1
        if success:
            self.payment_successes += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        uptime = time.time() - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "uptime_seconds": round(uptime, 2),
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "total_requests": self.request_count,
            "success_rate": round((self.success_count / max(self.request_count, 1)) * 100, 2),
            "error_rate": round((self.error_count / max(self.request_count, 1)) * 100, 2),
            "average_response_time": round(avg_response_time, 3),
            "ton_api_success_rate": round(((self.ton_api_calls - self.ton_api_errors) / max(self.ton_api_calls, 1)) * 100, 2),
            "payment_success_rate": round((self.payment_successes / max(self.payment_attempts, 1)) * 100, 2),
            "top_error_types": dict(sorted(self.error_types.items(), key=lambda x: x[1], reverse=True)[:5]),
            "active_users": len(self.user_activity),
            "most_active_users": dict(sorted(self.user_activity.items(), key=lambda x: x[1], reverse=True)[:5])
        }

class HealthChecker:
    """Monitors bot health and system resources"""
    
    def __init__(self):
        self.logger = get_logger("HealthChecker")
        self.health_status = "unknown"
        self.last_check = None
        self.check_interval = 300  # 5 minutes
        self.health_history = deque(maxlen=50)
        
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        current_time = time.time()
        
        # Don't check too frequently
        if self.last_check and (current_time - self.last_check) < self.check_interval:
            return self.get_last_health_status()
        
        self.last_check = current_time
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "checks": {}
        }
        
        try:
            # Check database connectivity
            db_health = await self._check_database_health()
            health_status["checks"]["database"] = db_health
            
            # Check TON API health
            ton_health = await self._check_ton_api_health()
            health_status["checks"]["ton_api"] = ton_health
            
            # Check memory usage
            memory_health = self._check_memory_health()
            health_status["checks"]["memory"] = memory_health
            
            # Determine overall status
            overall_status = self._determine_overall_health(health_status["checks"])
            health_status["overall_status"] = overall_status
            
            # Store health status
            self.health_status = overall_status
            self.health_history.append(health_status)
            
            self.logger.info(f"Health check completed: {overall_status}")
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)
            return health_status
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            import sqlite3
            start_time = time.time()
            
            conn = sqlite3.connect('cgspins.db')
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            response_time = time.time() - start_time
            conn.close()
            
            return {
                "status": "healthy",
                "response_time": round(response_time, 3),
                "user_count": user_count,
                "details": "Database connection successful"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": "Database connection failed"
            }
    
    async def _check_ton_api_health(self) -> Dict[str, Any]:
        """Check TON API health"""
        try:
            from src.services.ton_api import TONAPIClient
            
            async with TONAPIClient() as client:
                health = await client.health_check()
                return health
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": "TON API health check failed"
            }
    
    def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory usage and performance"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                "status": "healthy" if memory.percent < 80 else "warning",
                "memory_percent": round(memory.percent, 1),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "cpu_percent": round(cpu_percent, 1),
                "details": f"Memory: {memory.percent}%, CPU: {cpu_percent}%"
            }
            
        except ImportError:
            return {
                "status": "unknown",
                "details": "psutil not available for memory monitoring"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": "Memory check failed"
            }
    
    def _determine_overall_health(self, checks: Dict[str, Any]) -> str:
        """Determine overall health status based on individual checks"""
        if not checks:
            return "unknown"
        
        statuses = [check.get("status", "unknown") for check in checks.values()]
        
        if "unhealthy" in statuses:
            return "unhealthy"
        elif "warning" in statuses:
            return "warning"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "degraded"
    
    def get_last_health_status(self) -> Dict[str, Any]:
        """Get the most recent health status"""
        if self.health_history:
            return self.health_history[-1]
        return {"overall_status": "unknown", "message": "No health checks performed yet"}

class AlertSystem:
    """Handles alerts and notifications for critical issues"""
    
    def __init__(self):
        self.logger = get_logger("AlertSystem")
        self.alert_history = deque(maxlen=100)
        self.alert_thresholds = {
            "error_rate": 20.0,  # Alert if error rate > 20%
            "response_time": 5.0,  # Alert if avg response time > 5s
            "ton_api_errors": 10,  # Alert if > 10 TON API errors
            "consecutive_failures": 5  # Alert if > 5 consecutive failures
        }
    
    def check_alerts(self, metrics: BotMetrics, health_status: str) -> List[Dict[str, Any]]:
        """Check if any alerts should be triggered"""
        alerts = []
        
        # Check error rate
        error_rate = metrics.error_count / max(metrics.request_count, 1) * 100
        if error_rate > self.alert_thresholds["error_rate"]:
            alerts.append({
                "level": "warning",
                "type": "high_error_rate",
                "message": f"Error rate is {error_rate:.1f}% (threshold: {self.alert_thresholds['error_rate']}%)",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check response time
        if metrics.response_times:
            avg_response_time = sum(metrics.response_times) / len(metrics.response_times)
            if avg_response_time > self.alert_thresholds["response_time"]:
                alerts.append({
                    "level": "warning",
                    "type": "slow_response",
                    "message": f"Average response time is {avg_response_time:.2f}s (threshold: {self.alert_thresholds['response_time']}s)",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Check TON API errors
        if metrics.ton_api_errors > self.alert_thresholds["ton_api_errors"]:
            alerts.append({
                "level": "error",
                "type": "ton_api_issues",
                "message": f"TON API has {metrics.ton_api_errors} errors",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check overall health
        if health_status == "unhealthy":
            alerts.append({
                "level": "critical",
                "type": "system_unhealthy",
                "message": "System health check failed",
                "timestamp": datetime.now().isoformat()
            })
        
        # Store alerts
        for alert in alerts:
            self.alert_history.append(alert)
            self.logger.warning(f"Alert: {alert['message']}")
        
        return alerts

# Global instances
metrics = BotMetrics()
health_checker = HealthChecker()
alert_system = AlertSystem() 