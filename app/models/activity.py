"""
Activity Models
Pydantic models for activity data validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ActivityBase(BaseModel):
    """Base activity model"""
    strava_id: int = Field(..., description="Strava activity ID")
    name: str = Field(..., description="Activity name")
    distance: float = Field(..., description="Distance in meters")
    moving_time: int = Field(..., description="Moving time in seconds")
    total_elevation_gain: float = Field(..., description="Total elevation gain in meters")
    activity_type: str = Field(..., description="Type of activity")
    start_date: datetime = Field(..., description="Activity start date")

class ActivityCreate(ActivityBase):
    """Model for creating a new activity"""
    user_id: int = Field(..., description="User ID")
    average_speed: Optional[float] = Field(None, description="Average speed in m/s")
    max_speed: Optional[float] = Field(None, description="Maximum speed in m/s")
    average_heartrate: Optional[float] = Field(None, description="Average heart rate")
    max_heartrate: Optional[float] = Field(None, description="Maximum heart rate")
    calories: Optional[float] = Field(None, description="Calories burned")
    kudos_count: int = Field(default=0, description="Number of kudos")

class ActivityUpdate(BaseModel):
    """Model for updating activity data"""
    name: Optional[str] = None
    distance: Optional[float] = None
    moving_time: Optional[int] = None
    total_elevation_gain: Optional[float] = None
    activity_type: Optional[str] = None
    start_date: Optional[datetime] = None
    average_speed: Optional[float] = None
    max_speed: Optional[float] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    calories: Optional[float] = None
    kudos_count: Optional[int] = None

class ActivityResponse(ActivityBase):
    """Model for activity response"""
    id: str = Field(..., description="Internal activity ID")
    user_id: int = Field(..., description="User ID")
    average_speed: Optional[float] = None
    max_speed: Optional[float] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    calories: Optional[float] = None
    kudos_count: int = Field(default=0)
    created_at: datetime = Field(..., description="When activity was created")
    updated_at: datetime = Field(..., description="When activity was last updated")
    insights: Optional[dict] = Field(None, description="AI-generated insights")

class ActivityStats(BaseModel):
    """Model for activity statistics"""
    total_activities: int = Field(..., description="Total number of activities")
    total_distance: float = Field(..., description="Total distance in meters")
    total_time: int = Field(..., description="Total time in seconds")
    total_elevation: float = Field(..., description="Total elevation gain in meters")
    average_distance: float = Field(..., description="Average distance per activity")
    average_time: int = Field(..., description="Average time per activity")
    favorite_activity_type: str = Field(..., description="Most common activity type")
    longest_activity: Optional[dict] = Field(None, description="Longest activity details")
    fastest_activity: Optional[dict] = Field(None, description="Fastest activity details")
    most_elevation_activity: Optional[dict] = Field(None, description="Activity with most elevation")
