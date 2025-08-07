import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.stravaai
users_collection = db.users

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
