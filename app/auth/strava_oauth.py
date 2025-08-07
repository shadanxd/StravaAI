"""
Strava OAuth Module
Handles Strava OAuth flow, token exchange, and user data extraction
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, PlainTextResponse
from authlib.integrations.starlette_client import OAuth
import os
import httpx
from dotenv import load_dotenv
from datetime import datetime
from app.auth.jwt import create_jwt_token
from app.database.db_operations import get_user_by_strava_id, create_user, update_user_tokens
from app.utils.encryption import encrypt_token, decrypt_token

load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI")

strava_oauth_router = APIRouter()

oauth = OAuth()
oauth.register(
    name='strava',
    client_id=STRAVA_CLIENT_ID,
    client_secret=STRAVA_CLIENT_SECRET,
    access_token_url='https://www.strava.com/oauth/token',
    access_token_params=None,
    authorize_url='https://www.strava.com/oauth/authorize',
    authorize_params=None,
    api_base_url='https://www.strava.com/api/v3/',
    client_kwargs={'scope': 'read,activity:read_all'},
)

def is_strava_token_expired(token_data):
    """Check if Strava access token is expired"""
    if not token_data or "expires_at" not in token_data:
        return True
    
    # Add 5 minute buffer before expiry
    buffer_time = 5 * 60  # 5 minutes in seconds
    return datetime.utcnow().timestamp() > (token_data["expires_at"] - buffer_time)

async def refresh_strava_access_token(refresh_token):
    """Refresh expired Strava access token using refresh token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )
        
        if response.status_code == 200:
            return response.json()
        return None

async def exchange_code_for_tokens(code: str):
    """Exchange authorization code for access and refresh tokens"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Token exchange failed: {response.text}"
            )
        
        return response.json()

async def save_user_tokens(user_data: dict, tokens: dict):
    """Save or update user tokens in database"""
    strava_id = user_data.get("id")
    
    # Encrypt tokens for secure storage
    encrypted_access_token = encrypt_token(tokens.get("access_token"))
    encrypted_refresh_token = encrypt_token(tokens.get("refresh_token"))
    
    # Check if user exists in database
    existing_user = await get_user_by_strava_id(strava_id)
    
    if existing_user:
        # Update existing user's tokens
        await update_user_tokens(
            strava_id=strava_id,
            access_token=encrypted_access_token,
            refresh_token=encrypted_refresh_token,
            expires_at=datetime.fromtimestamp(tokens.get("expires_at"))
        )
    else:
        # Create new user in database with complete user info
        user_data_for_db = {
            "strava_id": strava_id,
            "username": user_data.get("username", ""),
            "firstname": user_data.get("firstname", ""),
            "lastname": user_data.get("lastname", ""),
            "email": user_data.get("email"),
            "city": user_data.get("city"),
            "country": user_data.get("country"),
            "state": user_data.get("state"),
            "sex": user_data.get("sex"),
            "weight": user_data.get("weight"),
            "profile": user_data.get("profile"),
            "profile_medium": user_data.get("profile_medium"),
            "access_token": encrypted_access_token,
            "refresh_token": encrypted_refresh_token,
            "token_expires_at": datetime.fromtimestamp(tokens.get("expires_at"))
        }
        await create_user(user_data_for_db)

@strava_oauth_router.get("/api/auth/strava/authorize-url")
async def strava_authorize_url(request: Request):
    """Get Strava authorization URL for testing"""
    redirect_uri = STRAVA_REDIRECT_URI
    url = await oauth.strava.authorize_redirect(
        request,
        redirect_uri,
        approval_prompt="auto",
        scope="read,activity:read_all",
        response_type="code"
    )
    return PlainTextResponse(str(url.headers["location"]))

@strava_oauth_router.get("/api/auth/strava/authorize")
async def strava_authorize(request: Request):
    """Initiate Strava OAuth flow"""
    # Check if user already has valid tokens
    if "strava_tokens" in request.session:
        token_data = request.session["strava_tokens"]
        
        # If tokens are still valid, redirect to success
        if not is_strava_token_expired(token_data):
            user_info = token_data.get("athlete", {})
            jwt_token = create_jwt_token(
                user_id=user_info.get("id"),
                username=user_info.get("username", "")
            )
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            return RedirectResponse(
                url=f"{frontend_url}/auth/success?token={jwt_token}",
                status_code=302
            )
        
        # If tokens are expired but we have refresh token, try to refresh
        if "refresh_token" in token_data:
            refreshed_tokens = await refresh_strava_access_token(token_data["refresh_token"])
            if refreshed_tokens:
                # Update session with new tokens
                request.session["strava_tokens"] = refreshed_tokens
                user_info = refreshed_tokens.get("athlete", {})
                jwt_token = create_jwt_token(
                    user_id=user_info.get("id"),
                    username=user_info.get("username", "")
                )
                frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
                return RedirectResponse(
                    url=f"{frontend_url}/auth/success?token={jwt_token}",
                    status_code=302
                )
    
    # If no valid tokens or refresh failed, proceed with OAuth
    redirect_uri = STRAVA_REDIRECT_URI
    return await oauth.strava.authorize_redirect(
        request,
        redirect_uri,
        approval_prompt="force",
        scope="read,activity:read_all",
        response_type="code"
    )

@strava_oauth_router.get("/exchange_token")
async def strava_callback(request: Request):
    """Handle Strava OAuth callback and token exchange"""
    # Get the authorization code from the query parameters
    code = request.query_params.get("code")
    if not code:
        return JSONResponse({"error": "Missing authorization code"}, status_code=400)
    
    try:
        # Exchange the code for access token
        token_data = await exchange_code_for_tokens(code)
        user_info = token_data.get("athlete", {})
        strava_id = user_info.get("id")
        
        # Save user and tokens to database
        await save_user_tokens(user_info, token_data)
        
        # Create JWT token for frontend
        jwt_token = create_jwt_token(
            user_id=strava_id,
            username=user_info.get("username", "")
        )
        
        # Store JWT token in session
        request.session["jwt_token"] = jwt_token
        
        # Redirect to frontend with JWT token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{frontend_url}/auth/success?token={jwt_token}",
            status_code=302
        )
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            {"error": f"Authentication failed: {str(e)}"},
            status_code=500
        )

@strava_oauth_router.get("/auth/success")
async def auth_success(request: Request):
    """Success page after OAuth - tokens are stored in session"""
    if "strava_tokens" not in request.session:
        return JSONResponse({"error": "No authentication found"}, status_code=401)
    
    # Return only safe user info (no tokens)
    user_info = request.session["strava_tokens"].get("athlete", {})
    return JSONResponse({
        "message": "Authentication successful!",
        "user": {
            "id": user_info.get("id"),
            "username": user_info.get("username"),
            "firstname": user_info.get("firstname"),
            "lastname": user_info.get("lastname"),
            "city": user_info.get("city"),
            "country": user_info.get("country")
        }
    })
