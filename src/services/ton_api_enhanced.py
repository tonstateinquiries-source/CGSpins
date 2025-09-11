"""
Enhanced TON API service with circuit breaker, caching, and performance optimizations
Maintains 100% compatibility with existing functionality
"""

import asyncio
import time
import aiohttp
from typing import Dict, List, Any, Optional
import config
from src.utils.logger import get_logger
from src.utils.circuit_breaker import get_ton_api_breaker, with_circuit_breaker
from src.utils.cache import cache_manager
from src.utils.performance import track_performance, track_async_operation

logger = get_logger("TONAPI")

class TONAPIClient:
    """Enhanced TON API client with circuit breaker and caching"""
    
    def __init__(self, api_base=None, api_key=None, timeout=None):
        self.ton_api_base = config.TON_API_BASE
        self.ton_api_key = config.TON_API_KEY
        self.ton_api_timeout = config.TON_API_TIMEOUT
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1
        
        # Circuit breaker
        self.breaker = get_ton_api_breaker()
        
        # Session for connection reuse
        self._session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.ton_api_timeout),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
    
    @track_performance("ton_api")
    async def _make_ton_api_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make request to TON API with circuit breaker and caching"""
        # Create cache key
        cache_key = f"{endpoint}_{hash(str(params))}"
        
        # Try cache first
        cached_response = cache_manager.get_ton_api_data(endpoint, str(params))
        if cached_response is not None:
            logger.debug(f"Cache hit for TON API: {endpoint}")
            return cached_response
        
        # Use circuit breaker for the actual request
        try:
            response = await self.breaker.call(self._execute_request, endpoint, params)
            
            # Cache successful responses
            if response.get("ok", False):
                cache_manager.set_ton_api_data(endpoint, str(params), response)
            
            return response
            
        except Exception as e:
            logger.error(f"TON API request failed: {e}")
            return {"ok": False, "error": str(e)}
    
    async def _execute_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the actual HTTP request"""
        url = f"{self.ton_api_base}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.ton_api_key}"}
        request_params = params or {}
        
        logger.debug(f"TON API request: {url}, params={request_params}")
        
        async with self._session.get(url, params=request_params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return {"ok": True, "data": data}
            
            # Handle specific HTTP errors
            if response.status == 429:  # Rate limit
                logger.warning(f"TON API rate limited: {response.status}")
                raise Exception(f"Rate limit exceeded: {response.status}")
            elif response.status >= 500:  # Server error
                logger.error(f"TON API server error: {response.status}")
                raise Exception(f"Server error: {response.status}")
            else:
                error_text = await response.text()
                logger.error(f"TON API HTTP error {response.status}: {error_text}")
                return {"ok": False, "error": f"HTTP {response.status}"}
    
    @track_performance("ton_api")
    async def get_transactions_with_pagination(self, address: str, limit: int = 100, max_pages: int = 5) -> List[Dict[str, Any]]:
        """Get transactions with pagination and caching"""
        all_transactions = []
        offset = 0
        
        for page in range(max_pages):
            params = {
                "account": address,
                "limit": min(limit, 100),  # API limit is 100 per request
                "offset": offset
            }
            
            response = await self._make_ton_api_request("v2/accounts/{}/events".format(address), params)
            
            if not response.get("ok", False):
                logger.error(f"Failed to fetch transactions page {page + 1}: {response.get('error')}")
                break
            
            events = response.get("data", {}).get("events", [])
            if not events:
                break
            
            # Extract transactions from events
            for event in events:
                if event.get("actions"):
                    for action in event["actions"]:
                        if action.get("type") == "TonTransfer":
                            all_transactions.append({
                                "hash": event.get("event_id", ""),
                                "in_msg": {
                                    "msg_type": "int_msg",
                                    "value": action.get("amount", 0),
                                    "decoded_body": {
                                        "text": action.get("comment", "")
                                    },
                                    "source": {
                                        "address": action.get("sender", {}).get("address", "")
                                    }
                                },
                                "success": True
                            })
            
            offset += len(events)
            
            # If we got fewer events than requested, we've reached the end
            if len(events) < min(limit, 100):
                break
        
        logger.info(f"Fetched {len(all_transactions)} transactions from {max_pages} pages")
        return all_transactions
    
    @track_performance("ton_api")
    async def get_wallet_balance(self, address: str) -> Dict[str, Any]:
        """Get wallet balance with caching"""
        # Try cache first
        cache_key = f"balance_{address}"
        cached_balance = cache_manager.get_ton_api_data("balance", address)
        if cached_balance is not None:
            return cached_balance
        
        response = await self._make_ton_api_request(f"v2/accounts/{address}")
        
        if response.get("ok", False):
            balance_data = response.get("data", {})
            balance = balance_data.get("balance", 0)
            
            result = {
                "ok": True,
                "balance": balance,
                "address": address
            }
            
            # Cache balance for 30 seconds
            cache_manager.set_ton_api_data("balance", address, result)
            return result
        else:
            return {"ok": False, "error": response.get("error", "Unknown error")}
    
    @track_performance("ton_api")
    async def check_transaction_confirmation(self, tx_hash: str) -> Dict[str, Any]:
        """Check transaction confirmation with caching"""
        # Try cache first
        cached_confirmation = cache_manager.get_ton_api_data("confirmation", tx_hash)
        if cached_confirmation is not None:
            return cached_confirmation
        
        response = await self._make_ton_api_request(f"v2/blockchain/transactions/{tx_hash}")
        
        if response.get("ok", False):
            tx_data = response.get("data", {})
            is_confirmed = tx_data.get("success", False)
            
            result = {
                "ok": True,
                "is_confirmed": is_confirmed,
                "tx_hash": tx_hash
            }
            
            # Cache confirmation for 10 seconds (shorter TTL for dynamic data)
            cache_manager.set_ton_api_data("confirmation", tx_hash, result)
            return result
        else:
            return {"ok": False, "error": response.get("error", "Unknown error")}
    
    @track_performance("ton_api")
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on TON API"""
        try:
            start_time = time.time()
            
            # Try a simple API call
            response = await self._make_ton_api_request("v2/accounts/EQAlSNKjRlmJ1nz86lRKyqap39BiJ39LF1DkmqjXb-EL22D6")
            
            response_time = time.time() - start_time
            
            if response.get("ok", False):
                return {
                    "status": "healthy",
                    "response_time": round(response_time, 3),
                    "details": "TON API is responding normally"
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": response.get("error", "Unknown error"),
                    "response_time": round(response_time, 3),
                    "details": "TON API returned error"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": "TON API health check failed"
            }
    
    @track_performance("ton_api")
    async def test_api_connection(self) -> Dict[str, Any]:
        """Test API connection"""
        try:
            response = await self._make_ton_api_request("v2/accounts/EQAlSNKjRlmJ1nz86lRKyqap39BiJ39LF1DkmqjXb-EL22D6")
            return {"ok": response.get("ok", False), "error": response.get("error")}
        except Exception as e:
            return {"ok": False, "error": str(e)}
