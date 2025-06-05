import uuid
from typing import Dict, Any, List
from datetime import datetime
from models.api_models import (
    CreateActivityRequest, Activity, CreateClubRequest, UpdateClubRequest, 
    Club, CreateChallengeRequest, Challenge, SessionResponse
)

class MockScaffoldApiService:
    """Mock API service for development and testing."""
    
    def __init__(self):
        self.activities = []
        self.clubs = []
        self.challenges = []
        self.session_token = None
    
    async def set_session_token(self, token: str):
        """Set session token for authentication."""
        self.session_token = token
    
    # Authentication
    async def get_session(self) -> Dict[str, Any]:
        """Get current user session."""
        return {
            "data": {
                "user": {
                    "id": "mock-user-123",
                    "email": "test@example.com",
                    "name": "Test User",
                    "profile": {
                        "id": "profile-123",
                        "name": "Test User",
                        "bio": "Fitness enthusiast",
                        "avatar_url": None
                    }
                }
            }
        }
    
    # Activities
    async def get_activities(self) -> Dict[str, Any]:
        """Get all activities for authenticated user."""
        return {
            "data": self.activities,
            "message": f"Retrieved {len(self.activities)} activities"
        }
    
    async def create_activity(self, activity_data: CreateActivityRequest) -> Dict[str, Any]:
        """Create a new activity."""
        activity_id = str(uuid.uuid4())
        activity = {
            "id": activity_id,
            "user_id": "mock-user-123",
            "type": activity_data.type,
            "distance": activity_data.distance,
            "duration": activity_data.duration,
            "date": activity_data.date,
            "location": activity_data.location,
            "notes": activity_data.notes,
            "created_at": datetime.now().isoformat()
        }
        self.activities.append(activity)
        
        return {
            "data": activity,
            "message": "Activity created successfully"
        }
    
    async def get_activities_with_details(self) -> Dict[str, Any]:
        """Get activities with detailed information."""
        detailed_activities = []
        for activity in self.activities:
            detailed_activities.append({
                **activity,
                "calories_burned": self._estimate_calories(activity),
                "pace": self._calculate_pace(activity)
            })
        
        return {
            "data": detailed_activities,
            "summary": {
                "total_activities": len(detailed_activities),
                "total_distance": sum(a.get("distance", 0) or 0 for a in detailed_activities),
                "total_duration": sum(a.get("duration", 0) or 0 for a in detailed_activities)
            }
        }
    
    def _estimate_calories(self, activity: Dict) -> int:
        """Estimate calories burned based on activity."""
        duration_minutes = (activity.get("duration", 0) or 0) / 60
        activity_type = activity.get("type", "")
        
        calories_per_minute = {
            "running": 12,
            "cycling": 8,
            "swimming": 10,
            "walking": 5,
            "yoga": 3,
            "strength_training": 6
        }
        
        rate = calories_per_minute.get(activity_type, 5)
        return int(duration_minutes * rate)
    
    def _calculate_pace(self, activity: Dict) -> str:
        """Calculate pace for distance-based activities."""
        distance = activity.get("distance")
        duration = activity.get("duration")
        
        if not distance or not duration:
            return "N/A"
        
        pace_minutes = (duration / 60) / distance
        minutes = int(pace_minutes)
        seconds = int((pace_minutes - minutes) * 60)
        
        return f"{minutes}:{seconds:02d} min/km"
    
    # Clubs
    async def get_clubs(self) -> Dict[str, Any]:
        """Get all clubs."""
        return {
            "data": self.clubs,
            "message": f"Retrieved {len(self.clubs)} clubs"
        }
    
    async def create_club(self, club_data: CreateClubRequest) -> Dict[str, Any]:
        """Create a new club."""
        club_id = str(uuid.uuid4())
        club = {
            "id": club_id,
            "name": club_data.name,
            "description": club_data.description,
            "is_private": club_data.is_private,
            "background_image_url": club_data.background_image_url,
            "creator_id": "mock-user-123",
            "created_at": datetime.now().isoformat(),
            "member_count": 1
        }
        self.clubs.append(club)
        
        return {
            "data": club,
            "message": "Club created successfully"
        }
    
    async def get_club(self, club_id: str) -> Dict[str, Any]:
        """Get club by ID."""
        club = next((c for c in self.clubs if c["id"] == club_id), None)
        if not club:
            return {"error": "Club not found"}
        
        return {
            "data": club,
            "message": "Club retrieved successfully"
        }
    
    async def update_club(self, club_id: str, club_data: UpdateClubRequest) -> Dict[str, Any]:
        """Update club."""
        club = next((c for c in self.clubs if c["id"] == club_id), None)
        if not club:
            return {"error": "Club not found"}
        
        # Update fields
        if club_data.name is not None:
            club["name"] = club_data.name
        if club_data.description is not None:
            club["description"] = club_data.description
        if club_data.is_private is not None:
            club["is_private"] = club_data.is_private
        
        return {
            "data": club,
            "message": "Club updated successfully"
        }
    
    async def delete_club(self, club_id: str) -> Dict[str, Any]:
        """Delete club."""
        club = next((c for c in self.clubs if c["id"] == club_id), None)
        if not club:
            return {"error": "Club not found"}
        
        self.clubs.remove(club)
        return {"success": True, "message": "Club deleted successfully"}
    
    # Challenges
    async def get_challenges(self) -> Dict[str, Any]:
        """Get all challenges."""
        return {
            "data": self.challenges,
            "message": f"Retrieved {len(self.challenges)} challenges"
        }
    
    async def create_challenge(self, challenge_data: CreateChallengeRequest) -> Dict[str, Any]:
        """Create a new challenge."""
        challenge_id = str(uuid.uuid4())
        challenge = {
            "id": challenge_id,
            "title": challenge_data.title,
            "description": challenge_data.description,
            "creator_id": "mock-user-123",
            "target_value": challenge_data.target_value,
            "unit": challenge_data.unit,
            "start_date": challenge_data.start_date,
            "end_date": challenge_data.end_date,
            "is_public": challenge_data.is_public,
            "participant_count": 1,
            "created_at": datetime.now().isoformat()
        }
        self.challenges.append(challenge)
        
        return {
            "data": challenge,
            "message": "Challenge created successfully"
        }

# Create a global mock API service instance
mock_api_service = MockScaffoldApiService() 