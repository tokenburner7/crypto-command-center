"""Shared async HTTP client with User-Agent and rate limiting."""
import asyncio
import time
import httpx
from typing import Optional

class RateLimiter:
    def __init__(self, calls_per_second: float = 1.0):
        self.rate = calls_per_second
        self.last_call = 0.0
    
    async def acquire(self):
        now = time.time()
        wait = max(0, (1.0 / self.rate) - (now - self.last_call))
        if wait > 0:
            await asyncio.sleep(wait)
        self.last_call = time.time()

class APIClient:
    def __init__(self, base_url: str = "", rate_limit: float = 1.0, timeout: int = 30):
        self.base_url = base_url
        self.limiter = RateLimiter(rate_limit)
        self.timeout = timeout
        self.default_headers = {
            "User-Agent": "CryptoCommandCenter/0.3 (personal dashboard)",
        }
    
    async def get(self, url: str, params: Optional[dict] = None, 
                  headers: Optional[dict] = None, retries: int = 3):
        await self.limiter.acquire()
        merged = {**self.default_headers, **(headers or {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(retries):
                try:
                    resp = await client.get(f"{self.base_url}{url}", params=params, headers=merged)
                    resp.raise_for_status()
                    return resp.json()
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
