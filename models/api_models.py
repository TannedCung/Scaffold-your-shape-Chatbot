from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Activity Models
class CreateActivityRequest(BaseModel):
    type: Literal["running", "cycling", "swimming", "walking", "yoga", "strength_training", "other"]
    distance: Optional[float] = Field(None, ge=0, description="Distance in kilometers")
    duration: Optional[int] = Field(None, ge=0, description="Duration in seconds")
    date: str = Field(..., description="Activity date and time in ISO format")
    location: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)

class Activity(BaseModel):
    id: str
    user_id: str
    type: str
    distance: Optional[float] = None
    duration: Optional[int] = None
    date: str
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: str

# Club Models
class CreateClubRequest(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    is_private: bool = False
    background_image_url: Optional[str] = None

class UpdateClubRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_private: Optional[bool] = None

class Club(BaseModel):
    id: str
    name: str
    description: str
    is_private: bool
    background_image_url: Optional[str] = None
    creator_id: str
    created_at: str
    member_count: int

# Challenge Models
class CreateChallengeRequest(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    target_value: float = Field(..., ge=0)
    unit: str
    start_date: str
    end_date: str
    is_public: bool = True

class Challenge(BaseModel):
    id: str
    title: str
    description: str
    creator_id: str
    target_value: float
    unit: str
    start_date: str
    end_date: str
    is_public: bool
    participant_count: int
    created_at: str

# User and Profile Models
class Profile(BaseModel):
    id: str
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class User(BaseModel):
    id: str
    email: str
    name: str
    profile: Optional[Profile] = None

class SessionResponse(BaseModel):
    user: User

# API Response Models
class ApiResponse(BaseModel):
    data: dict

class ApiError(BaseModel):
    error: str
    code: str
    details: Optional[dict] = None 