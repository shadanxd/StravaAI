"""
Database Operations
Handles all database operations for users, activities, and insights
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.stravaai
users_collection = db.users
activities_collection = db.activities

# User operations
async def get_user_by_strava_id(strava_id: int) -> Optional[Dict[str, Any]]:
    """Get user by Strava ID"""
    user = await users_collection.find_one({"strava_id": strava_id})
    return user

async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by internal ID"""
    user = await users_collection.find_one({"_id": user_id})
    return user

async def create_user(user_data: Dict[str, Any]) -> str:
    """Create new user in database"""
    user_data["created_at"] = datetime.utcnow()
    user_data["updated_at"] = datetime.utcnow()
    
    result = await users_collection.insert_one(user_data)
    return str(result.inserted_id)

async def update_user_tokens(
    strava_id: int,
    access_token: str,
    refresh_token: str,
    expires_at: datetime
) -> bool:
    """Update user's Strava tokens"""
    result = await users_collection.update_one(
        {"strava_id": strava_id},
        {
            "$set": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_expires_at": expires_at,
                "updated_at": datetime.utcnow()
            }
        }
    )
    return result.modified_count > 0

async def update_user_profile(strava_id: int, profile_data: Dict[str, Any]) -> bool:
    """Update user profile information"""
    result = await users_collection.update_one(
        {"strava_id": strava_id},
        {
            "$set": {
                **profile_data,
                "updated_at": datetime.utcnow()
            }
        }
    )
    return result.modified_count > 0

async def add_user_milestone(strava_id: int, milestone: Dict[str, Any]) -> bool:
    """Add milestone to user"""
    result = await users_collection.update_one(
        {"strava_id": strava_id},
        {
            "$push": {"milestones": milestone},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    return result.modified_count > 0

async def update_user_milestone(
    strava_id: int,
    milestone_id: str,
    milestone_data: Dict[str, Any]
) -> bool:
    """Update specific milestone"""
    result = await users_collection.update_one(
        {
            "strava_id": strava_id,
            "milestones._id": milestone_id
        },
        {
            "$set": {
                "milestones.$": {**milestone_data, "_id": milestone_id},
                "updated_at": datetime.utcnow()
            }
        }
    )
    return result.modified_count > 0

async def delete_user_milestone(strava_id: int, milestone_id: str) -> bool:
    """Delete specific milestone"""
    result = await users_collection.update_one(
        {"strava_id": strava_id},
        {
            "$pull": {"milestones": {"_id": milestone_id}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    return result.modified_count > 0

async def get_user_milestones(strava_id: int) -> list:
    """Get all milestones for user"""
    user = await users_collection.find_one(
        {"strava_id": strava_id},
        {"milestones": 1}
    )
    return user.get("milestones", []) if user else []

async def delete_user(strava_id: int) -> bool:
    """Delete user from database"""
    result = await users_collection.delete_one({"strava_id": strava_id})
    return result.deleted_count > 0

# Activity operations
async def get_activity_by_strava_id(strava_id: int) -> Optional[Dict[str, Any]]:
    """Get activity by Strava ID"""
    activity = await activities_collection.find_one({"strava_id": strava_id})
    return activity

async def get_activity_by_id(activity_id: str) -> Optional[Dict[str, Any]]:
    """Get activity by internal ID"""
    activity = await activities_collection.find_one({"_id": activity_id})
    return activity

async def create_activity(activity_data: Dict[str, Any]) -> str:
    """Create new activity in database"""
    activity_data["created_at"] = datetime.utcnow()
    activity_data["updated_at"] = datetime.utcnow()
    
    result = await activities_collection.insert_one(activity_data)
    return str(result.inserted_id)

async def update_activity(
    strava_id: int,
    activity_data: Dict[str, Any]
) -> bool:
    """Update activity data"""
    result = await activities_collection.update_one(
        {"strava_id": strava_id},
        {
            "$set": {
                **activity_data,
                "updated_at": datetime.utcnow()
            }
        }
    )
    return result.modified_count > 0

async def get_user_activities(
    user_id: int,
    page: int = 1,
    per_page: int = 30,
    activity_type: Optional[str] = None,
    after: Optional[datetime] = None,
    before: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Get activities for a user with pagination and filtering"""
    query = {"user_id": user_id}
    
    if activity_type:
        query["activity_type"] = activity_type
    
    if after:
        query["start_date"] = {"$gte": after}
    
    if before:
        if "start_date" in query:
            query["start_date"]["$lte"] = before
        else:
            query["start_date"] = {"$lte": before}
    
    skip = (page - 1) * per_page
    
    cursor = activities_collection.find(query).sort("start_date", -1).skip(skip).limit(per_page)
    activities = await cursor.to_list(length=per_page)
    return activities

async def get_user_activity_stats(user_id: int) -> Dict[str, Any]:
    """Get activity statistics for a user"""
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "total_activities": {"$sum": 1},
                "total_distance": {"$sum": "$distance"},
                "total_time": {"$sum": "$moving_time"},
                "total_elevation": {"$sum": "$total_elevation_gain"},
                "total_calories": {"$sum": {"$ifNull": ["$calories", 0]}},
                "activities_by_type": {
                    "$push": "$activity_type"
                }
            }
        }
    ]
    
    result = await activities_collection.aggregate(pipeline).to_list(length=1)
    
    if not result:
        return {
            "total_activities": 0,
            "total_distance": 0,
            "total_time": 0,
            "total_elevation": 0,
            "total_calories": 0,
            "activities_by_type": {},
            "average_distance": 0,
            "average_time": 0
        }
    
    stats = result[0]
    
    # Calculate activities by type
    activities_by_type = {}
    for activity_type in stats["activities_by_type"]:
        activities_by_type[activity_type] = activities_by_type.get(activity_type, 0) + 1
    
    # Calculate averages
    total_activities = stats["total_activities"]
    average_distance = stats["total_distance"] / total_activities if total_activities > 0 else 0
    average_time = stats["total_time"] / total_activities if total_activities > 0 else 0
    
    return {
        "total_activities": total_activities,
        "total_distance": stats["total_distance"],
        "total_time": stats["total_time"],
        "total_elevation": stats["total_elevation"],
        "total_calories": stats["total_calories"],
        "activities_by_type": activities_by_type,
        "average_distance": average_distance,
        "average_time": average_time
    }

async def get_user_longest_activity(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's longest activity by distance"""
    activity = await activities_collection.find_one(
        {"user_id": user_id},
        sort=[("distance", -1)]
    )
    return activity

async def get_user_fastest_activity(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's fastest activity by average speed"""
    activity = await activities_collection.find_one(
        {"user_id": user_id, "average_speed": {"$exists": True, "$ne": None}},
        sort=[("average_speed", -1)]
    )
    return activity

async def get_user_most_elevation_activity(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's activity with most elevation gain"""
    activity = await activities_collection.find_one(
        {"user_id": user_id},
        sort=[("total_elevation_gain", -1)]
    )
    return activity

async def sync_user_activities(user_id: int, activities: List[Dict[str, Any]]) -> Dict[str, int]:
    """Sync activities for a user (upsert)"""
    created_count = 0
    updated_count = 0
    
    for activity in activities:
        strava_id = activity["strava_id"]
        existing_activity = await get_activity_by_strava_id(strava_id)
        
        if existing_activity:
            # Update existing activity
            await update_activity(strava_id, activity)
            updated_count += 1
        else:
            # Create new activity
            await create_activity(activity)
            created_count += 1
    
    return {
        "created": created_count,
        "updated": updated_count,
        "total": len(activities)
    }

async def delete_activity(strava_id: int) -> bool:
    """Delete activity from database"""
    result = await activities_collection.delete_one({"strava_id": strava_id})
    return result.deleted_count > 0

async def delete_user_activities(user_id: int) -> int:
    """Delete all activities for a user"""
    result = await activities_collection.delete_many({"user_id": user_id})
    return result.deleted_count
