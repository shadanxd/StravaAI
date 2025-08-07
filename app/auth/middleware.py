"""
JWT Middleware Module
Handles JWT token extraction from session cookies and user context injection
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.auth.jwt import validate_jwt_token, is_jwt_token_expired
from app.database.db_operations import get_user_by_strava_id
from app.utils.encryption import decrypt_token
from app.auth.strava_oauth import refresh_strava_access_token
from datetime import datetime

async def extract_jwt_from_session(request: Request):
    """Extract JWT token from session cookies"""
    jwt_token = request.session.get("jwt_token")
    if not jwt_token:
        return None
    return jwt_token

async def validate_and_inject_user(request: Request):
    """Validate JWT token and inject user context into request"""
    jwt_token = await extract_jwt_from_session(request)
    if not jwt_token:
        return None
    
    try:
        # Validate JWT token
        user_info = validate_jwt_token(jwt_token)
        user_id = user_info.get("user_id")
        
        # Get user from database using strava_id
        user = await get_user_by_strava_id(user_id)
        if not user:
            return None
        
        # Check if Strava tokens are expired and try to refresh
        if is_strava_token_expired({"expires_at": user["token_expires_at"].timestamp()}):
            # Decrypt refresh token
            decrypted_refresh_token = decrypt_token(user["refresh_token"])
            refreshed_tokens = await refresh_strava_access_token(decrypted_refresh_token)
            
            if refreshed_tokens:
                # Update tokens in database
                from app.utils.encryption import encrypt_token
                from app.database.db_operations import update_user_tokens
                
                encrypted_access_token = encrypt_token(refreshed_tokens.get("access_token"))
                encrypted_refresh_token = encrypt_token(refreshed_tokens.get("refresh_token"))
                
                await update_user_tokens(
                    strava_id=user["strava_id"],
                    access_token=encrypted_access_token,
                    refresh_token=encrypted_refresh_token,
                    expires_at=datetime.fromtimestamp(refreshed_tokens.get("expires_at"))
                )
                
                # Update user data
                user = await get_user_by_strava_id(user["strava_id"])
            else:
                return None
        
        # Inject user into request state
        request.state.user = user
        return user
        
    except HTTPException:
        return None
    except Exception:
        return None

async def get_current_user(request: Request):
    """Get current user from request context"""
    user = await validate_and_inject_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def get_optional_user(request: Request):
    """Get current user from request context (optional)"""
    return await validate_and_inject_user(request)
