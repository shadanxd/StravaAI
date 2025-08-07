"""
User Models
Pydantic models for user data validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    """Base user model"""
    strava_id: int = Field(..., description="Strava user ID")
    username: str = Field(..., description="Strava username")
    firstname: str = Field(..., description="User's first name")
    lastname: str = Field(..., description="User's last name")
    email: Optional[str] = Field(None, description="User's email")
    city: Optional[str] = Field(None, description="User's city")
    country: Optional[str] = Field(None, description="User's country")
    state: Optional[str] = Field(None, description="User's state")
    sex: Optional[str] = Field(None, description="User's sex")
    weight: Optional[float] = Field(None, description="User's weight in kg")
    profile: Optional[str] = Field(None, description="Profile picture URL")
    profile_medium: Optional[str] = Field(None, description="Medium profile picture URL")

class UserCreate(UserBase):
    """Model for creating a new user"""
    access_token: str = Field(..., description="Encrypted access token")
    refresh_token: str = Field(..., description="Encrypted refresh token")
    token_expires_at: datetime = Field(..., description="Token expiration time")

class UserUpdate(BaseModel):
    """Model for updating user data"""
    username: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    sex: Optional[str] = None
    weight: Optional[float] = None
    profile: Optional[str] = None
    profile_medium: Optional[str] = None

class UserResponse(UserBase):
    """Model for user response (no sensitive data)"""
    id: str = Field(..., description="Internal user ID")
    created_at: datetime = Field(..., description="Account creation time")
    updated_at: datetime = Field(..., description="Last update time")
    milestones: List[dict] = Field(default=[], description="User milestones")

class Milestone(BaseModel):
    """Model for user milestones"""
    id: str = Field(..., description="Milestone ID")
    title: str = Field(..., description="Milestone title")
    description: Optional[str] = Field(None, description="Milestone description")
    type: str = Field(..., description="Milestone type")
    achieved_at: datetime = Field(..., description="When milestone was achieved")
    data: Optional[dict] = Field(None, description="Milestone data")
