"""
Authentication Dependencies
FastAPI dependency injection for user authentication and authorization
"""
from fastapi import Depends, Request, HTTPException
from app.auth.middleware import get_current_user, get_optional_user

def require_authentication():
    """Dependency that requires authentication"""
    return get_current_user

def optional_authentication():
    """Dependency that allows optional authentication"""
    return get_optional_user

# Common dependency aliases
CurrentUser = Depends(require_authentication())
OptionalUser = Depends(optional_authentication())
