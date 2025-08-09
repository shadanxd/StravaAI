"""
JWT Authentication Module
Handles JWT token creation, validation, and user context extraction
"""
from datetime import datetime, timedelta
import jwt as pyjwt
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-jwt-key")

def create_jwt_token(user_id: int, username: str):
    """Create JWT token for frontend authentication"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=7),  # 7 days expiry
        "iat": datetime.utcnow()
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_jwt_token(token: str):
    """Decode JWT token and return payload"""
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def validate_jwt_token(token: str):
    """Validate JWT token and return user info"""
    payload = decode_jwt_token(token)
    user_id = payload.get("user_id")
    username = payload.get("username")
    
    if not user_id or not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return {
        "user_id": user_id,
        "username": username
    }

def is_jwt_token_expired(token: str):
    """Check if JWT token is expired"""
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return False
    except pyjwt.ExpiredSignatureError:
        return True
    except pyjwt.InvalidTokenError:
        return True

def decode_jwt_token_allow_expired(token: str):
    """Decode JWT token but ignore expiration to recover payload (e.g., to refresh).

    SECURITY NOTE: Only use this server-side when you intend to immediately re-issue
    a new JWT or to look up the user for a server-side token refresh. Do not use
    the result of this function to authorize requests.
    """
    try:
        payload = pyjwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        return payload
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
