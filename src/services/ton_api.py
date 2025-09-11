"""
TON API service for CG Spins Bot
Enhanced with professional error handling and retry mechanisms
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
import config
from src.utils import get_logger, ErrorRecovery, TONAPIError


class TONAPIClient:
    def __init__(self, api_base=None, api_key=None, timeout=None):
        # TON API (tonapi.io) only
        self.ton_api_base = "https://tonapi.io"
        self.ton_api_key = config.TON_API_KEY  # Use config instead of hardcoded value
        self.ton_api_timeout = 30
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1
        
        # Initialize logger
        self.logger = get_logger("TONAPIClient")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def _make_ton_api_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make request to TON API with enhanced error handling and retry logic"""
        
        async def make_request():
            try:
                import requests
                
                def sync_request():
                    url = f"{self.ton_api_base}/{endpoint}"
                    headers = {"Authorization": f"Bearer {self.ton_api_key}"}
                    request_params = params or {}
                    
                    self.logger.info(f"TON API request: {url}, params={request_params}")
                    response = requests.get(url, params=request_params, headers=headers, timeout=self.ton_api_timeout)
                    
                    if response.status_code == 200:
                        return response.json()
                    
                    # Handle specific HTTP errors
                    if response.status_code == 429:  # Rate limit
                        self.logger.warning(f"TON API rate limited: {response.status_code}")
                        raise TONAPIError(f"Rate limit exceeded: {response.status_code}")
                    elif response.status_code >= 500:  # Server error
                        self.logger.error(f"TON API server error: {response.status_code}")
                        raise TONAPIError(f"Server error: {response.status_code}")
                    else:
                        self.logger.error(f"TON API HTTP error {response.status_code}: {response.text}")
                        return {"ok": False, "error": f"HTTP {response.status_code}"}
                
                return await asyncio.to_thread(sync_request)
                        
            except TONAPIError:
                raise  # Re-raise TON-specific errors
            except Exception as e:
                self.logger.error(f"TON API request failed: {e}")
                return {"ok": False, "error": str(e)}
        
        # Use retry mechanism for failed requests
        try:
            return await ErrorRecovery.retry_with_backoff(
                make_request, 
                max_retries=self.max_retries, 
                base_delay=self.base_delay
            )
        except Exception as e:
            self.logger.error(f"All retry attempts failed for {endpoint}: {e}")
            return {"ok": False, "error": f"All retries failed: {str(e)}"}
    
    async def get_transactions_with_pagination(self, address: str, limit: int = 100, max_pages: int = 5) -> List[Dict[str, Any]]:
        """Get transactions using TON API"""
        print(f"📄 [Backend] Fetching transactions for {address[:20]}...")
        
        txs = await self._get_transactions_ton_api(address, limit, max_pages)
        
        if txs and len(txs) > 0:
            print(f"✅ [Backend] TON API successful: {len(txs)} transactions")
            return txs
            
        print("❌ [Backend] TON API failed to fetch transactions")
        return []
        
    async def _get_transactions_ton_api(self, address: str, limit: int, max_pages: int) -> List[Dict[str, Any]]:
        """Get transactions using TON API"""
        try:
            # First, get the raw address from TON API using account info
            print(f"🔍 [Backend] Converting EQ address to raw format...")
            account_info = await self._make_ton_api_request(f"v2/blockchain/accounts/{address}")
            
            if not account_info or "address" not in account_info:
                print(f"❌ [Backend] Could not get account info for {address}")
                return []
                
            raw_address = account_info["address"]
            print(f"✅ [Backend] Converted {address[:20]}... to raw: {raw_address[:20]}...")
            
            all_txs = []
            offset = 0
            
            for page in range(max_pages):
                params = {
                    'limit': min(limit, 100),
                    'offset': offset
                }
                
                print(f"📄 [Backend] TON API page {page+1}/{max_pages}, offset={offset}")
                data = await self._make_ton_api_request(f"v2/blockchain/accounts/{raw_address}/transactions", params)
            
                if not data or "transactions" not in data:
                    print(f"❌ [Backend] TON API error: {data.get('error', 'Unknown')}")
                    break
                    
                txs = data.get("transactions", [])
                if not txs:
                    print(f"📭 [Backend] No more txs on TON API page {page+1}")
                    break
                    
                all_txs.extend(txs)
                print(f" - Got {len(txs)} txs, total={len(all_txs)}")
                
                if len(all_txs) >= limit:
                    break
                    
                offset += len(txs)
                
            print(f"📄 [Backend] TON API fetched {len(all_txs)} transactions")
            return all_txs
                
        except Exception as e:
            print(f"❌ [Backend] TON API pagination failed: {e}")
            return []
    
    async def check_transaction_confirmation(self, tx_hash: str) -> Dict[str, Any]:
        """Check transaction confirmation using TON API"""
        try:
            print(f"🔎 [Backend] Checking confirmation for tx {tx_hash[:10]}...")
            
            data = await self._make_ton_api_request(f"v2/blockchain/transactions/{tx_hash}")
            
            if data and "block" in data:
                block_info = data.get("block", "")
                confirmed = "(" in block_info and ")" in block_info
                print(f" - TON API Status: {'Confirmed' if confirmed else 'Pending'}, block={block_info}")
                return {
                    "hash": tx_hash,
                    "is_confirmed": confirmed,
                    "block_info": block_info,
                    "status": "confirmed" if confirmed else "pending"
                }
                
            print(f" - Error: {data.get('error', 'Unknown')}")
            return {"hash": tx_hash, "is_confirmed": False, "error": data.get("error")}
                
        except Exception as e:
            print(f"❌ [Backend] Confirmation check failed for {tx_hash[:10]}: {e}")
            return {"hash": tx_hash, "is_confirmed": True, "error": str(e)}  # Fallback to confirmed
    
    async def get_wallet_balance(self, address: str) -> Dict[str, Any]:
        """Get wallet balance using TON API"""
        try:
            print(f"💰 [Backend] Getting balance for {address[:20]}...")
            
            data = await self._make_ton_api_request(f"v2/blockchain/accounts/{address}")
            
            if data and "balance" in data:
                balance = data.get("balance", 0)
                print(f" - TON API Balance: {balance / 1e9} TON")
                return {"ok": True, "balance": balance}
                
            return {"ok": False, "error": "TON API failed"}
                
        except Exception as e:
            print(f"❌ [Backend] Balance check failed: {e}")
            return {"ok": False, "error": str(e)}
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """Test TON API connection with enhanced error handling"""
        self.logger.info("Testing TON API connection...")
        try:
            # Simple test request
            result = await self._make_ton_api_request("v2/blockchain/accounts/EQAlSNKjRlmJ1nz86lRKyqap39BiJ39LF1DkmqjXb-EL22D6")
            if result and "address" in result:
                self.logger.info("TON API connection successful")
                return {"ok": True, "message": "TON API connection successful"}
            else:
                error_msg = result.get('error', 'Unknown error')
                self.logger.error(f"TON API connection failed: {error_msg}")
                return {"ok": False, "error": error_msg}
        except Exception as e:
            self.logger.error(f"TON API connection test failed: {e}")
            return {"ok": False, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for TON API"""
        self.logger.info("Performing TON API health check...")
        
        health_status = {
            "api_connection": False,
            "rate_limit_status": "unknown",
            "response_time": None,
            "overall_status": "unhealthy"
        }
        
        try:
            # Test connection
            start_time = time.time()
            connection_test = await self.test_api_connection()
            response_time = time.time() - start_time
            
            health_status["api_connection"] = connection_test.get("ok", False)
            health_status["response_time"] = round(response_time, 3)
            
            # Determine overall status
            if health_status["api_connection"] and health_status["response_time"] < 5.0:
                health_status["overall_status"] = "healthy"
            elif health_status["api_connection"]:
                health_status["overall_status"] = "degraded"
            else:
                health_status["overall_status"] = "unhealthy"
                
            self.logger.info(f"Health check completed: {health_status['overall_status']}")
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status["overall_status"] = "error"
            return health_status 