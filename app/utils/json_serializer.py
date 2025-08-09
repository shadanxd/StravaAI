"""
JSON Serializer Utilities
Converts MongoDB objects to JSON-serializable format
"""
from datetime import datetime
from typing import Any, Dict, List, Union
from bson import ObjectId

def serialize_datetime(obj: datetime) -> str:
    """Convert datetime to ISO format string"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def serialize_object_id(obj: Any) -> str:
    """Convert ObjectId to string"""
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

def to_json_serializable(doc: Any) -> Any:
    """Convert nested structures containing datetime/ObjectId to JSON-serializable primitives"""
    if not doc:
        return doc
    
    if isinstance(doc, list):
        # Handle lists
        return [to_json_serializable(item) for item in doc]
    elif isinstance(doc, dict):
        # Handle dictionaries
        serialized = {}
        for key, value in doc.items():
            if isinstance(value, datetime):
                serialized[key] = serialize_datetime(value)
            elif isinstance(value, ObjectId):
                serialized[key] = serialize_object_id(value)
            elif isinstance(value, dict):
                serialized[key] = to_json_serializable(value)
            elif isinstance(value, list):
                serialized[key] = to_json_serializable(value)
            else:
                serialized[key] = value
        return serialized
    else:
        # Handle other types
        if isinstance(doc, datetime):
            return serialize_datetime(doc)
        elif isinstance(doc, ObjectId):
            return serialize_object_id(doc)
        else:
            return doc

def serialize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize user document for API response"""
    if not user:
        return user
    
    return {
        "id": user.get("strava_id"),
        "username": user.get("username"),
        "firstname": user.get("firstname"),
        "lastname": user.get("lastname"),
        "city": user.get("city"),
        "country": user.get("country"),
        "state": user.get("state"),
        "email": user.get("email"),
        "age": user.get("age"),
        "weight": user.get("weight"),
        "sex": user.get("sex"),
        "profile": user.get("profile"),
        "profile_medium": user.get("profile_medium"),
        "milestones": to_json_serializable(user.get("milestones", [])),
        "created_at": serialize_datetime(user.get("created_at")),
        "updated_at": serialize_datetime(user.get("updated_at"))
    }

def serialize_milestone(milestone: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize milestone document for API response"""
    if not milestone:
        return milestone
    
    return {
        "id": milestone.get("id"),
        "title": milestone.get("title"),
        "description": milestone.get("description"),
        "type": milestone.get("type"),
        "achieved_at": serialize_datetime(milestone.get("achieved_at")),
        "data": milestone.get("data"),
        "created_at": serialize_datetime(milestone.get("created_at")),
        "updated_at": serialize_datetime(milestone.get("updated_at"))
    }

def serialize_activity(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize activity document for API response"""
    if not activity:
        return activity
    
    return {
        "id": serialize_object_id(activity.get("_id")),
        "strava_id": activity.get("strava_id"),
        "name": activity.get("name"),
        "distance": activity.get("distance"),
        "moving_time": activity.get("moving_time"),
        "total_elevation_gain": activity.get("total_elevation_gain"),
        "activity_type": activity.get("activity_type"),
        "start_date": serialize_datetime(activity.get("start_date")),
        "average_speed": activity.get("average_speed"),
        "max_speed": activity.get("max_speed"),
        "average_heartrate": activity.get("average_heartrate"),
        "max_heartrate": activity.get("max_heartrate"),
        "calories": activity.get("calories"),
        "kudos_count": activity.get("kudos_count", 0),
        "has_insights": bool(activity.get("insights")),
        "created_at": serialize_datetime(activity.get("created_at")),
        "updated_at": serialize_datetime(activity.get("updated_at"))
    }
