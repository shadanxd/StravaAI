"""
Base API Client
Common HTTP client functionality for API interactions
"""
import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class BaseAPIClient:
    """Base class for API clients with common HTTP functionality"""
    
    def __init__(self, base_url: str = "", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
    
    async def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    params=params
                )
                
                return await self.handle_response(response)
                
            except httpx.TimeoutException:
                logger.error(f"Request timeout for {url}")
                raise HTTPException(status_code=408, detail="Request timeout")
            except httpx.RequestError as e:
                logger.error(f"Request error for {url}: {str(e)}")
                raise HTTPException(status_code=500, detail="Request failed")
    
    async def handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response with error checking"""
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        elif response.status_code == 403:
            raise HTTPException(status_code=403, detail="Forbidden")
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="Not found")
        elif response.status_code == 429:
            raise HTTPException(status_code=429, detail="Rate limited")
        else:
            logger.error(f"API error {response.status_code}: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"API error: {response.text}"
            )
    
    def handle_errors(self, error: Exception) -> None:
        """Handle and log errors"""
        logger.error(f"API client error: {str(error)}")
        if isinstance(error, HTTPException):
            raise error
        else:
            raise HTTPException(status_code=500, detail="Internal server error")
