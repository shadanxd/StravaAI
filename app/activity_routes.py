"""
Activity Routes
Handles all activity-related endpoints
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime, timedelta
from app.auth.middleware import get_current_user
from app.database.db_operations import (
    get_user_by_strava_id,
    get_user_activities,
    get_activity_by_strava_id,
    get_activity_by_id,
    get_user_activity_stats,
    get_user_longest_activity,
    get_user_fastest_activity,
    get_user_most_elevation_activity,
    sync_user_activities
)
from app.models.activity import ActivityUpdate
from app.api.strava_client import StravaAPIClient
from app.utils.json_serializer import serialize_activity, to_json_serializable

# Create activity router
activity_router = APIRouter(prefix="/api/activities", tags=["activities"])

@activity_router.get("/")
async def get_activities(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=100, description="Items per page"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    after: Optional[datetime] = Query(None, description="Filter activities after this date"),
    before: Optional[datetime] = Query(None, description="Filter activities before this date")
):
    """Get current user's activities with pagination and filtering"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get activities from database
        activities = await get_user_activities(
            user_id=user_id,
            page=page,
            per_page=per_page,
            activity_type=activity_type,
            after=after,
            before=before
        )
        
        # Transform activities for response
        activity_list = [serialize_activity(activity) for activity in activities]
        
        return JSONResponse({
            "activities": activity_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(activity_list)
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activities: {str(e)}")

@activity_router.get("/id/{activity_id}")
async def get_activity(request: Request, activity_id: str = Path(..., description="Internal activity ID (Mongo ObjectId)")):
    """Get detailed information about a specific activity"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get activity from database
        activity = await get_activity_by_id(activity_id)
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        # Check if activity belongs to user
        if activity["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return JSONResponse({
            "activity": serialize_activity(activity)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity: {str(e)}")

@activity_router.get("/strava/{strava_id}")
async def get_activity_by_strava_id_endpoint(request: Request, strava_id: int):
    """Get activity by Strava ID"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get activity from database
        activity = await get_activity_by_strava_id(strava_id)
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        # Check if activity belongs to user
        if activity["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return JSONResponse(
            to_json_serializable({
                "activity": {
                    "id": str(activity["_id"]),
                    "strava_id": activity["strava_id"],
                    "name": activity["name"],
                    "distance": activity["distance"],
                    "moving_time": activity["moving_time"],
                    "elapsed_time": activity["elapsed_time"],
                    "total_elevation_gain": activity["total_elevation_gain"],
                    "activity_type": activity["activity_type"],
                    "start_date": activity["start_date"],
                    "start_date_local": activity["start_date_local"],
                    "timezone": activity["timezone"],
                    "start_latlng": activity.get("start_latlng"),
                    "end_latlng": activity.get("end_latlng"),
                    "location_city": activity.get("location_city"),
                    "location_state": activity.get("location_state"),
                    "location_country": activity.get("location_country"),
                    "achievement_count": activity.get("achievement_count", 0),
                    "kudos_count": activity.get("kudos_count", 0),
                    "comment_count": activity.get("comment_count", 0),
                    "trainer": activity.get("trainer", False),
                    "commute": activity.get("commute", False),
                    "manual": activity.get("manual", False),
                    "private": activity.get("private", False),
                    "average_speed": activity.get("average_speed"),
                    "max_speed": activity.get("max_speed"),
                    "average_cadence": activity.get("average_cadence"),
                    "average_temp": activity.get("average_temp"),
                    "average_watts": activity.get("average_watts"),
                    "kilojoules": activity.get("kilojoules"),
                    "has_heartrate": activity.get("has_heartrate", False),
                    "average_heartrate": activity.get("average_heartrate"),
                    "max_heartrate": activity.get("max_heartrate"),
                    "elev_high": activity.get("elev_high"),
                    "elev_low": activity.get("elev_low"),
                    "suffer_score": activity.get("suffer_score"),
                    "description": activity.get("description"),
                    "calories": activity.get("calories"),
                    "segment_efforts": activity.get("segment_efforts"),
                    "best_efforts": activity.get("best_efforts"),
                    "gear_id": activity.get("gear_id"),
                    "photos": activity.get("photos"),
                    "insights": activity.get("insights"),
                    "created_at": activity.get("created_at"),
                    "updated_at": activity.get("updated_at")
                }
            })
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity: {str(e)}")

@activity_router.get("/stats/summary")
async def get_activity_stats(request: Request):
    """Get activity statistics for current user (last 30 days), split by Run, Ride, Swim."""
    try:
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")

        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        async def build_sport_summary(sport: str):
            sport_stats = await get_user_activity_stats(
                user_id,
                activity_type=sport,
                after=start_date,
                before=end_date,
            )
            longest = await get_user_longest_activity(
                user_id,
                activity_type=sport,
                after=start_date,
                before=end_date,
            )
            fastest = await get_user_fastest_activity(
                user_id,
                activity_type=sport,
                after=start_date,
                before=end_date,
            )
            most_elev = await get_user_most_elevation_activity(
                user_id,
                activity_type=sport,
                after=start_date,
                before=end_date,
            )

            sport_stats["average_distance"] = round(sport_stats.get("average_distance", 0), 2)
            sport_stats["average_time"] = round(sport_stats.get("average_time", 0), 2)

            def summarize_activity(a):
                if not a:
                    return None
                return {
                    "id": str(a.get("_id")),
                    "strava_id": a.get("strava_id"),
                    "name": a.get("name"),
                    "distance": a.get("distance"),
                    "moving_time": a.get("moving_time"),
                    "total_elevation_gain": a.get("total_elevation_gain"),
                    "activity_type": a.get("activity_type"),
                    "start_date": a.get("start_date"),
                    "average_speed": a.get("average_speed"),
                    "max_speed": a.get("max_speed"),
                    "average_heartrate": a.get("average_heartrate"),
                    "max_heartrate": a.get("max_heartrate"),
                    "calories": a.get("calories"),
                    "kudos_count": a.get("kudos_count", 0),
                    "has_insights": bool(a.get("insights")),
                }

            return {
                "stats": sport_stats,
                "notable_activities": {
                    "longest_activity": summarize_activity(longest),
                    "fastest_activity": summarize_activity(fastest),
                    "most_elevation_activity": summarize_activity(most_elev),
                },
            }

        run_summary = await build_sport_summary("Run")
        ride_summary = await build_sport_summary("Ride")
        swim_summary = await build_sport_summary("Swim")

        return JSONResponse(
            to_json_serializable(
                {
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "days_back": 30,
                    },
                    "run": run_summary,
                    "ride": ride_summary,
                    "swim": swim_summary,
                }
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity stats: {str(e)}")

@activity_router.post("/sync")
async def sync_activities_from_strava(
    request: Request,
    days_back: int = Query(30, ge=1, le=365, description="Number of days to sync back")
):
    """Sync activities from Strava API"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Get activities from Strava (paginate with max page size to minimize calls)
        strava_client = StravaAPIClient()
        per_page = 200
        page = 1
        strava_activities: List[dict] = []
        while True:
            page_activities = await strava_client.get_user_activities(
                user=user,
                page=page,
                per_page=per_page,
                after=int(start_date.timestamp()),
                before=int(end_date.timestamp()),
            )
            if not page_activities:
                break
            strava_activities.extend(page_activities)
            if len(page_activities) < per_page:
                break
            page += 1
        
        if not strava_activities:
            return JSONResponse({
                "message": "No activities found in the specified date range",
                "sync_result": {
                    "created": 0,
                    "updated": 0,
                    "total": 0
                }
            })
        
        # Transform activities for database storage
        activities_to_sync = []
        for activity in strava_activities:
            activity_data = {
                # Store both keys for compatibility with existing code and unique index
                "strava_activity_id": int(activity["id"]),
                "strava_id": int(activity["id"]),
                "user_id": user_id,
                "name": activity["name"],
                "distance": activity["distance"],
                "moving_time": activity["moving_time"],
                "elapsed_time": activity["elapsed_time"],
                "total_elevation_gain": activity["total_elevation_gain"],
                "activity_type": activity["type"],
                "start_date": datetime.fromisoformat(activity["start_date"].replace("Z", "+00:00")),
                "start_date_local": datetime.fromisoformat(activity["start_date_local"].replace("Z", "+00:00")),
                "timezone": activity["timezone"],
                "utc_offset": activity["utc_offset"],
                "start_latlng": activity.get("start_latlng"),
                "end_latlng": activity.get("end_latlng"),
                "location_city": activity.get("location_city"),
                "location_state": activity.get("location_state"),
                "location_country": activity.get("location_country"),
                "achievement_count": activity.get("achievement_count", 0),
                "kudos_count": activity.get("kudos_count", 0),
                "comment_count": activity.get("comment_count", 0),
                "athlete_count": activity.get("athlete_count", 1),
                "photo_count": activity.get("photo_count", 0),
                "map_id": activity.get("map_id"),
                "trainer": activity.get("trainer", False),
                "commute": activity.get("commute", False),
                "manual": activity.get("manual", False),
                "private": activity.get("private", False),
                "flagged": activity.get("flagged", False),
                "workout_type": activity.get("workout_type"),
                "upload_id": activity.get("upload_id"),
                "external_id": activity.get("external_id"),
                "average_speed": activity.get("average_speed"),
                "max_speed": activity.get("max_speed"),
                "average_cadence": activity.get("average_cadence"),
                "average_temp": activity.get("average_temp"),
                "average_watts": activity.get("average_watts"),
                "weighted_average_watts": activity.get("weighted_average_watts"),
                "kilojoules": activity.get("kilojoules"),
                "device_watts": activity.get("device_watts", False),
                "has_heartrate": activity.get("has_heartrate", False),
                "average_heartrate": activity.get("average_heartrate"),
                "max_heartrate": activity.get("max_heartrate"),
                "elev_high": activity.get("elev_high"),
                "elev_low": activity.get("elev_low"),
                "suffer_score": activity.get("suffer_score"),
                "description": activity.get("description"),
                "calories": activity.get("calories"),
                "segment_efforts": activity.get("segment_efforts"),
                "best_efforts": activity.get("best_efforts"),
                "gear_id": activity.get("gear_id"),
                "photos": activity.get("photos"),
                "stats_visibility": activity.get("stats_visibility"),
                "hide_from_home": activity.get("hide_from_home", False),
                "raw_data": activity
            }
            activities_to_sync.append(activity_data)
        
        # Sync activities to database
        sync_result = await sync_user_activities(user_id, activities_to_sync)
        
        return JSONResponse({
            "message": "Activities synced successfully",
            "sync_result": sync_result,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_back": days_back
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync activities: {str(e)}")

@activity_router.get("/recent")
async def get_recent_activities(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="Number of recent activities")
):
    """Get recent activities for current user"""
    try:
        # Get user from JWT token
        user_info = await get_current_user(request)
        user_id = user_info.get("user_id")
        
        # Get user from database
        user = await get_user_by_strava_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get recent activities from database
        activities = await get_user_activities(
            user_id=user_id,
            page=1,
            per_page=limit
        )
        
        # Transform activities for response
        activity_list = [serialize_activity(activity) for activity in activities]
        
        return JSONResponse({
            "activities": activity_list,
            "count": len(activity_list)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent activities: {str(e)}")
