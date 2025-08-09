"""
Database Operations
Handles all database operations for users, activities, and insights
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, Dict, Any, List
from pymongo import UpdateOne
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
    # Create the update data explicitly
    update_data = {
        "username": profile_data.get("username"),
        "firstname": profile_data.get("firstname"),
        "lastname": profile_data.get("lastname"),
        "city": profile_data.get("city"),
        "country": profile_data.get("country"),
        "state": profile_data.get("state"),
        "sex": profile_data.get("sex"),
        "weight": profile_data.get("weight"),
        "profile": profile_data.get("profile"),
        "profile_medium": profile_data.get("profile_medium"),
        "updated_at": datetime.utcnow()
    }
    
    # Remove None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    result = await users_collection.update_one(
        {"strava_id": strava_id},
        {"$set": update_data}
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
            "milestones.id": milestone_id
        },
        {
            "$set": {
                "milestones.$": {**milestone_data, "id": milestone_id},
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
            "$pull": {"milestones": {"id": milestone_id}},
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
    activity = await activities_collection.find_one({
        "$or": [
            {"strava_activity_id": int(strava_id)},
            {"strava_id": int(strava_id)},
        ]
    })
    return activity

async def get_activity_by_id(activity_id: str) -> Optional[Dict[str, Any]]:
    """Get activity by internal ID"""
    activity = await activities_collection.find_one({"_id": activity_id})
    return activity

async def create_activity(activity_data: Dict[str, Any]) -> str:
    """Create new activity in database"""
    # Ensure consistent identifier fields
    if activity_data.get("strava_activity_id") is None and activity_data.get("strava_id") is not None:
        activity_data["strava_activity_id"] = int(activity_data["strava_id"])
    if activity_data.get("strava_id") is None and activity_data.get("strava_activity_id") is not None:
        activity_data["strava_id"] = int(activity_data["strava_activity_id"])

    activity_data["created_at"] = datetime.utcnow()
    activity_data["updated_at"] = datetime.utcnow()
    
    result = await activities_collection.insert_one(activity_data)
    return str(result.inserted_id)

async def update_activity(
    strava_id: int,
    activity_data: Dict[str, Any]
) -> bool:
    """Update activity data"""
    # Ensure both identifier fields stay in sync
    if activity_data.get("strava_activity_id") is None and activity_data.get("strava_id") is not None:
        activity_data["strava_activity_id"] = int(activity_data["strava_id"])
    if activity_data.get("strava_id") is None and activity_data.get("strava_activity_id") is not None:
        activity_data["strava_id"] = int(activity_data["strava_activity_id"])

    result = await activities_collection.update_one(
        {"$or": [
            {"strava_activity_id": int(strava_id)},
            {"strava_id": int(strava_id)},
        ]},
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

async def get_user_activity_stats(
    user_id: int,
    activity_type: Optional[str] = None,
    after: Optional[datetime] = None,
    before: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Get activity statistics for a user with optional filters."""
    match: Dict[str, Any] = {"user_id": user_id}
    if activity_type:
        match["activity_type"] = activity_type
    if after:
        match.setdefault("start_date", {})["$gte"] = after
    if before:
        match.setdefault("start_date", {})["$lte"] = before

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": None,
                "total_activities": {"$sum": 1},
                "total_distance": {"$sum": "$distance"},
                "total_time": {"$sum": "$moving_time"},
                "total_elevation": {"$sum": "$total_elevation_gain"},
                "total_calories": {"$sum": {"$ifNull": ["$calories", 0]}},
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
            "average_distance": 0,
            "average_time": 0,
        }

    stats = result[0]

    total_activities = stats["total_activities"]
    average_distance = stats["total_distance"] / total_activities if total_activities > 0 else 0
    average_time = stats["total_time"] / total_activities if total_activities > 0 else 0

    return {
        "total_activities": total_activities,
        "total_distance": stats["total_distance"],
        "total_time": stats["total_time"],
        "total_elevation": stats["total_elevation"],
        "total_calories": stats["total_calories"],
        "average_distance": average_distance,
        "average_time": average_time,
    }

async def get_analytics_summary(
    user_id: int,
    after: Optional[datetime] = None,
    before: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Return overall and per-sport analytics for a user within an optional date range.

    Uses a single $facet pipeline to compute totals and per-activity_type breakdown.
    """
    match: Dict[str, Any] = {"user_id": user_id}
    if after:
        match.setdefault("start_date", {})["$gte"] = after
    if before:
        match.setdefault("start_date", {})["$lte"] = before

    pipeline = [
        {"$match": match},
        {
            "$facet": {
                "summary": [
                    {
                        "$group": {
                            "_id": None,
                            "total_activities": {"$sum": 1},
                            "total_distance": {"$sum": "$distance"},
                            "total_time": {"$sum": "$moving_time"},
                            "total_elevation": {"$sum": "$total_elevation_gain"},
                            "total_calories": {"$sum": {"$ifNull": ["$calories", 0]}},
                        }
                    }
                ],
                "by_sport": [
                    {
                        "$group": {
                            "_id": "$activity_type",
                            "total_activities": {"$sum": 1},
                            "total_distance": {"$sum": "$distance"},
                            "total_time": {"$sum": "$moving_time"},
                            "total_elevation": {"$sum": "$total_elevation_gain"},
                            "total_calories": {"$sum": {"$ifNull": ["$calories", 0]}},
                        }
                    },
                    {"$sort": {"_id": 1}},
                ],
            }
        },
    ]

    result = await activities_collection.aggregate(pipeline).to_list(length=1)
    if not result:
        base = {
            "total_activities": 0,
            "total_distance": 0,
            "total_time": 0,
            "total_elevation": 0,
            "total_calories": 0,
        }
        return {"summary": {**base, "average_distance": 0, "average_time": 0}, "by_sport": []}

    data = result[0]
    summary_raw = (data.get("summary") or [{}])[0] if data.get("summary") else {}
    total_activities = summary_raw.get("total_activities", 0) or 0
    average_distance = (
        (summary_raw.get("total_distance", 0) or 0) / total_activities if total_activities > 0 else 0
    )
    average_time = (
        (summary_raw.get("total_time", 0) or 0) / total_activities if total_activities > 0 else 0
    )

    summary = {
        "total_activities": total_activities,
        "total_distance": summary_raw.get("total_distance", 0) or 0,
        "total_time": summary_raw.get("total_time", 0) or 0,
        "total_elevation": summary_raw.get("total_elevation", 0) or 0,
        "total_calories": summary_raw.get("total_calories", 0) or 0,
        "average_distance": average_distance,
        "average_time": average_time,
    }

    by_sport_docs: List[Dict[str, Any]] = data.get("by_sport") or []
    by_sport: List[Dict[str, Any]] = []
    for doc in by_sport_docs:
        cnt = doc.get("total_activities", 0) or 0
        by_sport.append(
            {
                "activity_type": doc.get("_id"),
                "total_activities": cnt,
                "total_distance": doc.get("total_distance", 0) or 0,
                "total_time": doc.get("total_time", 0) or 0,
                "total_elevation": doc.get("total_elevation", 0) or 0,
                "total_calories": doc.get("total_calories", 0) or 0,
                "average_distance": (doc.get("total_distance", 0) or 0) / cnt if cnt > 0 else 0,
                "average_time": (doc.get("total_time", 0) or 0) / cnt if cnt > 0 else 0,
            }
        )

    return {"summary": summary, "by_sport": by_sport}

async def get_trend_timeseries(
    user_id: int,
    metric: str = "distance",
    after: Optional[datetime] = None,
    before: Optional[datetime] = None,
    period: str = "day",
    activity_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return a timeseries for the selected metric aggregated by day/week/month.

    Supported metrics: distance, time, elevation, calories, count.
    Supported periods: day, week, month.
    """
    metric_field_map = {
        "distance": "$distance",
        "time": "$moving_time",
        "elevation": "$total_elevation_gain",
        "calories": {"$ifNull": ["$calories", 0]},
    }

    match: Dict[str, Any] = {"user_id": user_id}
    if activity_type:
        match["activity_type"] = activity_type
    if after:
        match.setdefault("start_date", {})["$gte"] = after
    if before:
        match.setdefault("start_date", {})["$lte"] = before

    if period not in {"day", "week", "month"}:
        period = "day"

    # Use $dateTrunc (MongoDB 5+) for clean period grouping
    date_trunc_unit = period
    period_expr = {"$dateTrunc": {"date": "$start_date", "unit": date_trunc_unit, "timezone": "UTC"}}

    if metric == "count":
        value_expr: Any = 1
    else:
        value_expr = metric_field_map.get(metric, "$distance")

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": period_expr,
                "value": {"$sum": value_expr},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "period_start": "$_id",
                "value": "$value",
                "count": "$count",
            }
        },
    ]

    docs = await activities_collection.aggregate(pipeline).to_list(length=None)
    return docs

async def get_user_longest_activity(
    user_id: int,
    activity_type: Optional[str] = None,
    after: Optional[datetime] = None,
    before: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    """Get user's longest activity by distance with optional filters."""
    query: Dict[str, Any] = {"user_id": user_id}
    if activity_type:
        query["activity_type"] = activity_type
    if after or before:
        query["start_date"] = {}
        if after:
            query["start_date"]["$gte"] = after
        if before:
            query["start_date"]["$lte"] = before
    activity = await activities_collection.find_one(query, sort=[("distance", -1)])
    return activity

async def get_user_fastest_activity(
    user_id: int,
    activity_type: Optional[str] = None,
    after: Optional[datetime] = None,
    before: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    """Get user's fastest activity by average speed with optional filters."""
    query: Dict[str, Any] = {
        "user_id": user_id,
        "average_speed": {"$exists": True, "$ne": None},
    }
    if activity_type:
        query["activity_type"] = activity_type
    if after or before:
        query["start_date"] = {}
        if after:
            query["start_date"]["$gte"] = after
        if before:
            query["start_date"]["$lte"] = before
    activity = await activities_collection.find_one(query, sort=[("average_speed", -1)])
    return activity

async def get_user_most_elevation_activity(
    user_id: int,
    activity_type: Optional[str] = None,
    after: Optional[datetime] = None,
    before: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    """Get user's activity with most elevation gain with optional filters."""
    query: Dict[str, Any] = {"user_id": user_id}
    if activity_type:
        query["activity_type"] = activity_type
    if after or before:
        query["start_date"] = {}
        if after:
            query["start_date"]["$gte"] = after
        if before:
            query["start_date"]["$lte"] = before
    activity = await activities_collection.find_one(query, sort=[("total_elevation_gain", -1)])
    return activity

async def sync_user_activities(user_id: int, activities: List[Dict[str, Any]]) -> Dict[str, int]:
    """Sync activities for a user using bulk upsert to avoid duplicates and minimize round-trips."""
    if not activities:
        return {"created": 0, "updated": 0, "total": 0}

    # Prepare bulk operations using the unique Strava activity identifier
    operations: List[UpdateOne] = []
    for activity in activities:
        # Backward/forward compatibility: prefer `strava_activity_id` if present, else use `strava_id`
        strava_activity_id = activity.get("strava_activity_id") or activity.get("strava_id")
        if strava_activity_id is None:
            # Skip malformed records that would violate unique index (null)
            continue

        # Ensure both fields are stored for consistency with docs/indexes and existing code paths
        activity["strava_activity_id"] = int(strava_activity_id)
        activity["strava_id"] = int(strava_activity_id)

        # Always maintain timestamps
        activity["updated_at"] = datetime.utcnow()
        if "created_at" not in activity:
            activity["created_at"] = datetime.utcnow()

        operations.append(
            UpdateOne(
                {"$or": [
                    {"strava_activity_id": int(strava_activity_id)},
                    {"strava_id": int(strava_activity_id)},
                ]},
                {"$set": activity},
                upsert=True,
            )
        )

    if not operations:
        return {"created": 0, "updated": 0, "total": 0}

    result = await activities_collection.bulk_write(operations, ordered=False)

    # Best-effort counts
    created_count = getattr(result, "upserted_count", 0) or 0
    updated_count = (getattr(result, "modified_count", 0) or 0)

    return {
        "created": created_count,
        "updated": updated_count,
        "total": created_count + updated_count,
    }

async def delete_activity(strava_id: int) -> bool:
    """Delete activity from database"""
    result = await activities_collection.delete_one({"strava_id": strava_id})
    return result.deleted_count > 0

async def delete_user_activities(user_id: int) -> int:
    """Delete all activities for a user"""
    result = await activities_collection.delete_many({"user_id": user_id})
    return result.deleted_count
