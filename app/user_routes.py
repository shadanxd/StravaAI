"""
User Routes
Handles all user-related endpoints (separate from authentication)
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime
from app.auth.middleware import get_current_user
from app.database.db_operations import (
    get_user_by_strava_id,
    update_user_profile,
    add_user_milestone,
    update_user_milestone,
    delete_user_milestone,
    get_user_milestones
)
from app.models.user import UserUpdate, Milestone
from app.api.strava_client import StravaAPIClient

# Create user router
user_router = APIRouter(prefix="/api/user", tags=["user"])

@user_router.get("/profile")
async def get_user_profile(request: Request):
    """Get current user's profile information"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
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
                "milestones": user.get("milestones", []),

            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")

@user_router.put("/profile")
async def update_user_profile(request: Request, user_update: UserUpdate):
    """Update current user's profile information"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data (only include non-None values)
        update_data = {}
        for field, value in user_update.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update user profile
        success = await update_user_profile(user_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update user profile")
        
        # Get updated user data
        updated_user = await get_user_by_strava_id(user_id)
        
        return JSONResponse({
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user["strava_id"],
                "username": updated_user["username"],
                "firstname": updated_user["firstname"],
                "lastname": updated_user["lastname"],
                "city": updated_user.get("city"),
                "country": updated_user.get("country"),
                "state": updated_user.get("state"),
                "email": updated_user.get("email"),
                "age": updated_user.get("age"),
                "weight": updated_user.get("weight"),
                "sex": updated_user.get("sex"),
                "profile": updated_user.get("profile"),
                "profile_medium": updated_user.get("profile_medium"),
                "milestones": updated_user.get("milestones", []),
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")

@user_router.get("/milestones")
async def get_user_milestones_list(request: Request):
    """Get all milestones for current user"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get milestones from database
        milestones = await get_user_milestones(user_id)
        
        return JSONResponse({
            "milestones": milestones
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get milestones: {str(e)}")

@user_router.post("/milestones")
async def create_user_milestone(request: Request, milestone: Milestone):
    """Create a new milestone for current user"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare milestone data
        milestone_data = milestone.dict()
        milestone_data["created_at"] = datetime.utcnow()
        
        # Add milestone to user
        success = await add_user_milestone(user_id, milestone_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create milestone")
        
        return JSONResponse({
            "message": "Milestone created successfully",
            "milestone": milestone_data
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create milestone: {str(e)}")

@user_router.put("/milestones/{milestone_id}")
async def update_user_milestone_endpoint(
    request: Request,
    milestone_id: str,
    milestone_update: Milestone
):
    """Update a specific milestone for current user"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare milestone data
        milestone_data = milestone_update.dict(exclude_unset=True)
        milestone_data["updated_at"] = datetime.utcnow()
        
        # Update milestone
        success = await update_user_milestone(user_id, milestone_id, milestone_data)
        if not success:
            raise HTTPException(status_code=404, detail="Milestone not found")
        
        return JSONResponse({
            "message": "Milestone updated successfully",
            "milestone_id": milestone_id
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update milestone: {str(e)}")

@user_router.delete("/milestones/{milestone_id}")
async def delete_user_milestone_endpoint(request: Request, milestone_id: str):
    """Delete a specific milestone for current user"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete milestone
        success = await delete_user_milestone(user_id, milestone_id)
        if not success:
            raise HTTPException(status_code=404, detail="Milestone not found")
        
        return JSONResponse({
            "message": "Milestone deleted successfully",
            "milestone_id": milestone_id
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete milestone: {str(e)}")

@user_router.post("/sync-profile")
async def sync_user_profile_from_strava(request: Request):
    """Sync user profile from Strava API"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get fresh profile from Strava
        strava_client = StravaAPIClient()
        strava_profile = await strava_client.get_user_profile(user)
        
        if not strava_profile:
            raise HTTPException(status_code=500, detail="Failed to fetch profile from Strava")
        
        # Update user profile with fresh data
        profile_data = {
            "username": strava_profile.get("username"),
            "firstname": strava_profile.get("firstname"),
            "lastname": strava_profile.get("lastname"),
            "city": strava_profile.get("city"),
            "country": strava_profile.get("country"),
            "state": strava_profile.get("state"),
            "email": strava_profile.get("email"),
            "weight": strava_profile.get("weight"),
            "sex": strava_profile.get("sex"),
            "profile": strava_profile.get("profile"),
            "profile_medium": strava_profile.get("profile_medium")
        }
        
        success = await update_user_profile(user_id, profile_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update user profile")
        
        return JSONResponse({
            "message": "Profile synced successfully from Strava",
            "profile": profile_data
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync profile: {str(e)}")
