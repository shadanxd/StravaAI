"""
JWT Middleware Module
Handles JWT token extraction from session cookies and user context injection
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.auth.jwt import (
    validate_jwt_token,
    is_jwt_token_expired,
    create_jwt_token,
    decode_jwt_token,
    decode_jwt_token_allow_expired,
)
from app.database.db_operations import get_user_by_strava_id
from app.utils.encryption import decrypt_token, encrypt_token
from app.auth.strava_oauth import refresh_strava_access_token, is_strava_token_expired
from app.database.db_operations import update_user_tokens
from datetime import datetime

async def extract_jwt_from_session(request: Request):
    """Extract JWT token from session cookies or Authorization header (Bearer)."""
    # Prefer session cookie
    jwt_token = request.session.get("jwt_token")
    if jwt_token:
        return jwt_token

    # Fallback to Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        return token or None
    return None

async def validate_and_inject_user(request: Request):
    """Validate JWT token and inject user context into request"""
    jwt_token = await extract_jwt_from_session(request)
    if not jwt_token:
        return None
    
    try:
        # First, try to validate JWT token normally
        try:
            user_info = validate_jwt_token(jwt_token)
            user_id = user_info.get("user_id")
            jwt_expired = False
        except HTTPException:
            # JWT is expired, decode without verifying exp to recover user_id
            try:
                payload = decode_jwt_token_allow_expired(jwt_token)
                user_id = payload.get("user_id")
                jwt_expired = True
                if not user_id:
                    return None
            except Exception:
                return None
        
        # Get user from database using strava_id
        user = await get_user_by_strava_id(user_id)
        if not user:
            return None
        
        # Check if Strava tokens are expired and try to refresh
        if is_strava_token_expired({"expires_at": user["token_expires_at"].timestamp()}):
            try:
                # Decrypt refresh token
                decrypted_refresh_token = decrypt_token(user["refresh_token"])
                if not decrypted_refresh_token:
                    return None
                
                refreshed_tokens = await refresh_strava_access_token(decrypted_refresh_token)
                
                if refreshed_tokens:
                    # Update tokens in database
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
            except Exception as e:
                print(f"Token refresh error in middleware: {str(e)}")
                return None
        
        # If JWT was expired, create a new one
        if jwt_expired:
            new_jwt_token = create_jwt_token(
                user_id=user["strava_id"],
                username=user["username"]
            )
            request.session["jwt_token"] = new_jwt_token
            user_info = {
                "user_id": user["strava_id"],
                "username": user["username"]
            }
        else:
            # JWT is valid, use the existing user_info
            user_info = {
                "user_id": user["strava_id"],
                "username": user["username"]
            }
        
        # Inject user into request state
        request.state.user = user
        return user_info
        
    except HTTPException:
        return None
    except Exception as e:
        print(f"Middleware error: {str(e)}")
        return None

async def get_current_user(request: Request):
    """Get current user from request context"""
    user_info = await validate_and_inject_user(request)
    if not user_info:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_info

async def get_optional_user(request: Request):
    """Get current user from request context (optional)"""
    return await validate_and_inject_user(request)
