"""
Authentication Routes
Handles all authentication-related endpoints with proper separation of JWT and Strava OAuth
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.auth.jwt import (
    create_jwt_token,
    validate_jwt_token,
    decode_jwt_token,
    decode_jwt_token_allow_expired,
)
from app.auth.strava_oauth import strava_oauth_router
from app.auth.middleware import get_current_user, get_optional_user
from app.database.db_operations import get_user_by_strava_id
from app.utils.encryption import decrypt_token
from app.auth.strava_oauth import refresh_strava_access_token
from app.utils.json_serializer import serialize_user
from datetime import datetime

# Create main auth router
auth_router = APIRouter()

# Include Strava OAuth routes
auth_router.include_router(strava_oauth_router)

@auth_router.get("/api/auth/user")
async def get_user_info(request: Request):
    """Get current user info using JWT token from session"""
    # Get JWT token from session
    jwt_token = request.session.get("jwt_token")
    if not jwt_token:
        return JSONResponse({"error": "No JWT token in session"}, status_code=401)
    
    try:
        # Get user from JWT token
        user_info = validate_jwt_token(jwt_token)
        user_id = user_info.get("user_id")
        
        # Get user from database using strava_id
        user = await get_user_by_strava_id(user_id)
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=401)
        
        # Check if tokens are expired and try to refresh
        from app.auth.strava_oauth import is_strava_token_expired
        
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
                return JSONResponse({"error": "Token expired and refresh failed"}, status_code=401)
        
        return JSONResponse({
            "user": serialize_user(user)
        })
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({"error": f"Authentication failed: {str(e)}"}, status_code=401)

@auth_router.get("/api/auth/status")
async def get_auth_status(request: Request):
    """Check if user is authenticated using JWT token from session"""
    # Get JWT token from session
    jwt_token = request.session.get("jwt_token")
    if not jwt_token:
        return JSONResponse({"authenticated": False})
    
    try:
        # Get user from JWT token
        user_info = validate_jwt_token(jwt_token)
        user_id = user_info.get("user_id")
        
        # Get user from database using strava_id
        user = await get_user_by_strava_id(user_id)
        if not user:
            return JSONResponse({"authenticated": False})
        
        # Check if tokens are expired and try to refresh
        from app.auth.strava_oauth import is_strava_token_expired
        
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
                return JSONResponse({"authenticated": False})
        
        return JSONResponse({
            "authenticated": True,
            "user": serialize_user(user)
        })
    except Exception:
        return JSONResponse({"authenticated": False})

@auth_router.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user (clear session)"""
    request.session.clear()
    return JSONResponse({"message": "Logged out successfully"})

@auth_router.post("/api/auth/refresh")
async def refresh_tokens(request: Request):
    """Manually refresh access tokens using JWT token from session"""
    # Get JWT token from session
    jwt_token = request.session.get("jwt_token")
    if not jwt_token:
        return JSONResponse({"error": "No JWT token in session"}, status_code=401)
    
    try:
        # Try to get user from JWT token (may be expired)
        try:
            user_info = validate_jwt_token(jwt_token)
            user_id = user_info.get("user_id")
        except HTTPException:
            # JWT is expired, try to decode it without verifying exp to get user_id
            try:
                payload = decode_jwt_token_allow_expired(jwt_token)
                user_id = payload.get("user_id")
                if not user_id:
                    return JSONResponse({"error": "Invalid JWT token"}, status_code=401)
            except Exception:
                return JSONResponse({"error": "Invalid JWT token"}, status_code=401)
        
        # Get user from database using strava_id
        user = await get_user_by_strava_id(user_id)
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=401)
        
        # Check if Strava tokens are expired
        from app.auth.strava_oauth import is_strava_token_expired
        
        # Support optional force refresh via query param or body
        force_param = request.query_params.get("force")
        force_refresh = False
        if force_param is not None:
            force_refresh = force_param.lower() in ("1", "true", "yes")
        else:
            try:
                body = await request.json()
                force_refresh = bool(body.get("force"))
            except Exception:
                force_refresh = False

        if force_refresh or is_strava_token_expired({"expires_at": user["token_expires_at"].timestamp()}):
            # Decrypt refresh token
            decrypted_refresh_token = decrypt_token(user["refresh_token"])
            if not decrypted_refresh_token:
                return JSONResponse({"error": "Invalid refresh token"}, status_code=401)
            
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
                
                # Create new JWT token
                new_jwt_token = create_jwt_token(
                    user_id=user["strava_id"],
                    username=user["username"]
                )
                
                # Update session with new JWT token
                request.session["jwt_token"] = new_jwt_token
                
                return JSONResponse({
                    "message": "Tokens refreshed successfully",
                    "new_jwt_token": new_jwt_token
                })
            else:
                return JSONResponse({"error": "Token refresh failed"}, status_code=401)
        else:
            # Tokens are still valid, just create a new JWT if needed
            try:
                validate_jwt_token(jwt_token)
                return JSONResponse({"message": "Tokens are still valid"})
            except HTTPException:
                # JWT is expired but Strava tokens are valid, create new JWT
                new_jwt_token = create_jwt_token(
                    user_id=user["strava_id"],
                    username=user["username"]
                )
                request.session["jwt_token"] = new_jwt_token
                
                return JSONResponse({
                    "message": "JWT token refreshed successfully",
                    "new_jwt_token": new_jwt_token
                })
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({"error": f"Authentication failed: {str(e)}"}, status_code=401)

# SECURITY: Removed direct refresh endpoint - never expose refresh tokens to client
# The refresh token should only be stored encrypted in the database and used server-side
