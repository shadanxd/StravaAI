"""
Authentication Routes
Handles all authentication-related endpoints with proper separation of JWT and Strava OAuth
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.auth.jwt import create_jwt_token, validate_jwt_token
from app.auth.strava_oauth import strava_oauth_router
from app.auth.middleware import get_current_user, get_optional_user
from app.database.db_operations import get_user_by_strava_id
from app.utils.encryption import decrypt_token
from app.auth.strava_oauth import refresh_strava_access_token
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
            "user": {
                "id": user["strava_id"],
                "username": user["username"],
                "firstname": user["firstname"],
                "lastname": user["lastname"],
                "city": user.get("city"),
                "country": user.get("country"),
                "state": user.get("state"),
                "email": user.get("email"),
                "age": user.get("age"),
                "weight": user.get("weight"),
                "sex": user.get("sex"),
                "profile": user.get("profile"),
                "profile_medium": user.get("profile_medium"),
                "milestones": user.get("milestones", [])
            }
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
            "user": {
                "id": user["strava_id"],
                "username": user["username"],
                "firstname": user["firstname"],
                "lastname": user["lastname"],
                "city": user.get("city"),
                "country": user.get("country"),
                "state": user.get("state"),
                "email": user.get("email"),
                "age": user.get("age"),
                "weight": user.get("weight"),
                "sex": user.get("sex"),
                "profile": user.get("profile"),
                "profile_medium": user.get("profile_medium"),
                "milestones": user.get("milestones", [])
            }
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
        # Get user from JWT token
        user_info = validate_jwt_token(jwt_token)
        user_id = user_info.get("user_id")
        
        # Get user from database using strava_id
        user = await get_user_by_strava_id(user_id)
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=401)
        
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
            
            return JSONResponse({"message": "Tokens refreshed successfully"})
        else:
            return JSONResponse({"error": "Token refresh failed"}, status_code=401)
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({"error": f"Authentication failed: {str(e)}"}, status_code=401)
