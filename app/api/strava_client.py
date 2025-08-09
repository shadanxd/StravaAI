"""
Strava API Client
Handles all Strava API interactions including token management
"""
from typing import Dict, Any, List, Optional
from app.api.base_client import BaseAPIClient
from app.utils.encryption import decrypt_token
from app.database.db_operations import get_user_by_strava_id, update_user_tokens
from app.auth.strava_oauth import refresh_strava_access_token
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

class StravaAPIClient(BaseAPIClient):
    """Strava API client for fetching user data and activities"""
    
    def __init__(self):
        super().__init__(base_url="https://www.strava.com/api/v3")
    
    async def get_valid_access_token(self, user: Dict[str, Any]) -> str:
        """Get valid access token for user, refresh if needed"""
        from app.auth.strava_oauth import is_strava_token_expired
        
        # Check if access token is expired
        if is_strava_token_expired({"expires_at": user["token_expires_at"].timestamp()}):
            # Token is expired, need to refresh
            decrypted_refresh_token = decrypt_token(user["refresh_token"])
            refreshed_tokens = await refresh_strava_access_token(decrypted_refresh_token)
            
            if refreshed_tokens:
                # Update tokens in database
                from app.utils.encryption import encrypt_token
                
                encrypted_access_token = encrypt_token(refreshed_tokens.get("access_token"))
                encrypted_refresh_token = encrypt_token(refreshed_tokens.get("refresh_token"))
                
                await update_user_tokens(
                    strava_id=user["strava_id"],
                    access_token=encrypted_access_token,
                    refresh_token=encrypted_refresh_token,
                    expires_at=datetime.fromtimestamp(refreshed_tokens.get("expires_at"))
                )
                
                return refreshed_tokens.get("access_token")
            else:
                raise Exception("Failed to refresh access token")
        
        # Token is still valid
        return decrypt_token(user["access_token"])
    
    async def get_user_profile(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Get user profile from Strava API"""
        access_token = await self.get_valid_access_token(user)

        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            return await self.make_request(
                method="GET",
                url=f"{self.base_url}/athlete",
                headers=headers
            )
        except Exception as e:
            # If unauthorized, try a one-time refresh and retry
            if getattr(e, "status_code", None) == 401:
                decrypted_refresh_token = decrypt_token(user["refresh_token"])
                refreshed_tokens = await refresh_strava_access_token(decrypted_refresh_token)
                if not refreshed_tokens:
                    raise
                # Persist new tokens
                from app.utils.encryption import encrypt_token
                encrypted_access_token = encrypt_token(refreshed_tokens.get("access_token"))
                encrypted_refresh_token = encrypt_token(refreshed_tokens.get("refresh_token"))
                await update_user_tokens(
                    strava_id=user["strava_id"],
                    access_token=encrypted_access_token,
                    refresh_token=encrypted_refresh_token,
                    expires_at=datetime.fromtimestamp(refreshed_tokens.get("expires_at"))
                )
                # Retry once
                headers = {"Authorization": f"Bearer {refreshed_tokens.get('access_token')}"}
                return await self.make_request(
                    method="GET",
                    url=f"{self.base_url}/athlete",
                    headers=headers
                )
            raise
    
    async def get_user_activities(
        self,
        user: Dict[str, Any],
        page: int = 1,
        per_page: int = 30,
        after: Optional[int] = None,
        before: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get user activities from Strava API"""
        access_token = await self.get_valid_access_token(user)

        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "page": page,
            "per_page": per_page
        }
        
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        
        try:
            return await self.make_request(
                method="GET",
                url=f"{self.base_url}/athlete/activities",
                headers=headers,
                params=params
            )
        except Exception as e:
            if getattr(e, "status_code", None) == 401:
                decrypted_refresh_token = decrypt_token(user["refresh_token"])
                refreshed_tokens = await refresh_strava_access_token(decrypted_refresh_token)
                if not refreshed_tokens:
                    raise
                from app.utils.encryption import encrypt_token
                encrypted_access_token = encrypt_token(refreshed_tokens.get("access_token"))
                encrypted_refresh_token = encrypt_token(refreshed_tokens.get("refresh_token"))
                await update_user_tokens(
                    strava_id=user["strava_id"],
                    access_token=encrypted_access_token,
                    refresh_token=encrypted_refresh_token,
                    expires_at=datetime.fromtimestamp(refreshed_tokens.get("expires_at"))
                )
                headers = {"Authorization": f"Bearer {refreshed_tokens.get('access_token')}"}
                return await self.make_request(
                    method="GET",
                    url=f"{self.base_url}/athlete/activities",
                    headers=headers,
                    params=params
                )
            raise
    
    async def get_activity_details(
        self,
        user: Dict[str, Any],
        activity_id: int
    ) -> Dict[str, Any]:
        """Get detailed activity information"""
        access_token = await self.get_valid_access_token(user)

        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            return await self.make_request(
                method="GET",
                url=f"{self.base_url}/activities/{activity_id}",
                headers=headers
            )
        except Exception as e:
            if getattr(e, "status_code", None) == 401:
                decrypted_refresh_token = decrypt_token(user["refresh_token"])
                refreshed_tokens = await refresh_strava_access_token(decrypted_refresh_token)
                if not refreshed_tokens:
                    raise
                from app.utils.encryption import encrypt_token
                encrypted_access_token = encrypt_token(refreshed_tokens.get("access_token"))
                encrypted_refresh_token = encrypt_token(refreshed_tokens.get("refresh_token"))
                await update_user_tokens(
                    strava_id=user["strava_id"],
                    access_token=encrypted_access_token,
                    refresh_token=encrypted_refresh_token,
                    expires_at=datetime.fromtimestamp(refreshed_tokens.get("expires_at"))
                )
                headers = {"Authorization": f"Bearer {refreshed_tokens.get('access_token')}"}
                return await self.make_request(
                    method="GET",
                    url=f"{self.base_url}/activities/{activity_id}",
                    headers=headers
                )
            raise
    
    async def get_activity_streams(
        self,
        user: Dict[str, Any],
        activity_id: int,
        keys: List[str] = None
    ) -> Dict[str, Any]:
        """Get activity streams (GPS data, heart rate, etc.)"""
        access_token = await self.get_valid_access_token(user)

        headers = {"Authorization": f"Bearer {access_token}"}
        params = {}
        
        if keys:
            params["keys"] = ",".join(keys)
        
        try:
            return await self.make_request(
                method="GET",
                url=f"{self.base_url}/activities/{activity_id}/streams",
                headers=headers,
                params=params
            )
        except Exception as e:
            if getattr(e, "status_code", None) == 401:
                decrypted_refresh_token = decrypt_token(user["refresh_token"])
                refreshed_tokens = await refresh_strava_access_token(decrypted_refresh_token)
                if not refreshed_tokens:
                    raise
                from app.utils.encryption import encrypt_token
                encrypted_access_token = encrypt_token(refreshed_tokens.get("access_token"))
                encrypted_refresh_token = encrypt_token(refreshed_tokens.get("refresh_token"))
                await update_user_tokens(
                    strava_id=user["strava_id"],
                    access_token=encrypted_access_token,
                    refresh_token=encrypted_refresh_token,
                    expires_at=datetime.fromtimestamp(refreshed_tokens.get("expires_at"))
                )
                headers = {"Authorization": f"Bearer {refreshed_tokens.get('access_token')}"}
                return await self.make_request(
                    method="GET",
                    url=f"{self.base_url}/activities/{activity_id}/streams",
                    headers=headers,
                    params=params
                )
            raise
    
    async def get_user_stats(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Get user statistics and totals"""
        access_token = await self.get_valid_access_token(user)

        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            return await self.make_request(
                method="GET",
                url=f"{self.base_url}/athletes/{user['strava_id']}/stats",
                headers=headers
            )
        except Exception as e:
            if getattr(e, "status_code", None) == 401:
                decrypted_refresh_token = decrypt_token(user["refresh_token"])
                refreshed_tokens = await refresh_strava_access_token(decrypted_refresh_token)
                if not refreshed_tokens:
                    raise
                from app.utils.encryption import encrypt_token
                encrypted_access_token = encrypt_token(refreshed_tokens.get("access_token"))
                encrypted_refresh_token = encrypt_token(refreshed_tokens.get("refresh_token"))
                await update_user_tokens(
                    strava_id=user["strava_id"],
                    access_token=encrypted_access_token,
                    refresh_token=encrypted_refresh_token,
                    expires_at=datetime.fromtimestamp(refreshed_tokens.get("expires_at"))
                )
                headers = {"Authorization": f"Bearer {refreshed_tokens.get('access_token')}"}
                return await self.make_request(
                    method="GET",
                    url=f"{self.base_url}/athletes/{user['strava_id']}/stats",
                    headers=headers
                )
            raise
