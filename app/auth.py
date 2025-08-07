from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse, PlainTextResponse
from authlib.integrations.starlette_client import OAuth
import os
import httpx
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import jwt as pyjwt

load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-jwt-key")

auth_router = APIRouter()

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

def create_jwt_token(user_id: int, username: str):
    """Create JWT token for frontend authentication"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=7),  # 7 days expiry
        "iat": datetime.utcnow()
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")

@auth_router.get("/api/auth/strava/authorize-url")
async def strava_authorize_url(request: Request):
    # Use Authlib to build the authorization URL, but do not redirect
    redirect_uri = STRAVA_REDIRECT_URI
    # Build the URL with custom parameters
    url = await oauth.strava.authorize_redirect(
        request,
        redirect_uri,
        approval_prompt="force",
        scope="read,activity:read_all",
        response_type="code"
    )
    # Instead of redirecting, return the URL as plain text for inspection
    return PlainTextResponse(str(url.headers["location"]))

@auth_router.get("/api/auth/strava/authorize")
async def strava_authorize(request: Request):
    redirect_uri = STRAVA_REDIRECT_URI
    return await oauth.strava.authorize_redirect(
        request,
        redirect_uri,
        approval_prompt="force",
        scope="read,activity:read_all",
        response_type="code"
    )

@auth_router.get("/exchange_token")
async def strava_callback(request: Request):
    # Get the authorization code from the query parameters
    code = request.query_params.get("code")
    if not code:
        return JSONResponse({"error": "Missing authorization code"}, status_code=400)
    
    # Exchange the code for access token using manual HTTP request
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
            return JSONResponse(
                {"error": "Token exchange failed", "details": response.text},
                status_code=response.status_code
            )
        
        token_data = response.json()
        
        # Store tokens securely in session (encrypted by SessionMiddleware)
        request.session["strava_tokens"] = token_data
        request.session["strava_user_id"] = token_data.get("athlete", {}).get("id")
        
        # Create JWT token for frontend
        user_info = token_data.get("athlete", {})
        jwt_token = create_jwt_token(
            user_id=user_info.get("id"),
            username=user_info.get("username", "")
        )
        
        # Redirect to frontend with JWT token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{frontend_url}/auth/success?token={jwt_token}",
            status_code=302
        )

@auth_router.get("/auth/success")
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

@auth_router.get("/api/auth/user")
async def get_user_info(request: Request):
    """Get current user info (tokens stored in session)"""
    if "strava_tokens" not in request.session:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    
    user_info = request.session["strava_tokens"].get("athlete", {})
    return JSONResponse({
        "user": {
            "id": user_info.get("id"),
            "username": user_info.get("username"),
            "firstname": user_info.get("firstname"),
            "lastname": user_info.get("lastname"),
            "city": user_info.get("city"),
            "country": user_info.get("country")
        }
    })

@auth_router.get("/api/auth/status")
async def get_auth_status(request: Request):
    """Check if user is authenticated (for frontend)"""
    if "strava_tokens" not in request.session:
        return JSONResponse({"authenticated": False})
    
    user_info = request.session["strava_tokens"].get("athlete", {})
    return JSONResponse({
        "authenticated": True,
        "user": {
            "id": user_info.get("id"),
            "username": user_info.get("username"),
            "firstname": user_info.get("firstname"),
            "lastname": user_info.get("lastname"),
            "city": user_info.get("city"),
            "country": user_info.get("country")
        }
    })

@auth_router.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user (clear session)"""
    request.session.clear()
    return JSONResponse({"message": "Logged out successfully"})
