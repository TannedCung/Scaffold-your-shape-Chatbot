import httpx
from typing import Dict, Any, List, Optional
from config.settings import settings
from models.api_models import (
    CreateActivityRequest, Activity, CreateClubRequest, UpdateClubRequest, 
    Club, CreateChallengeRequest, Challenge, SessionResponse, ApiError
)

class ScaffoldApiService:
    def __init__(self):
        self.base_url = settings.exercise_service_url
        self.session_token = None  # Should be set from authentication
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.session_token:
            headers["Cookie"] = f"next-auth.session-token={self.session_token}"
        return headers
    
    async def set_session_token(self, token: str):
        """Set session token for authentication."""
        self.session_token = token
    
    # Authentication
    async def get_session(self) -> Dict[str, Any]:
        """Get current user session."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/auth/session",
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    # Activities
    async def get_activities(self) -> Dict[str, Any]:
        """Get all activities for authenticated user."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/activities",
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    async def create_activity(self, activity_data: CreateActivityRequest) -> Dict[str, Any]:
        """Create a new activity."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/activities",
                    json=activity_data.dict(),
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    async def get_activities_with_details(self) -> Dict[str, Any]:
        """Get activities with detailed information."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/activities/with-details",
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    # Clubs
    async def get_clubs(self) -> Dict[str, Any]:
        """Get all clubs."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/clubs",
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    async def create_club(self, club_data: CreateClubRequest) -> Dict[str, Any]:
        """Create a new club."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/clubs",
                    json=club_data.dict(),
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    async def get_club(self, club_id: str) -> Dict[str, Any]:
        """Get club by ID."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/clubs/{club_id}",
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    async def update_club(self, club_id: str, club_data: UpdateClubRequest) -> Dict[str, Any]:
        """Update club."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    f"{self.base_url}/clubs/{club_id}",
                    json=club_data.dict(exclude_unset=True),
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    async def delete_club(self, club_id: str) -> Dict[str, Any]:
        """Delete club."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/clubs/{club_id}",
                    headers=self._get_headers()
                )
                if response.status_code == 204:
                    return {"success": True}
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    # Challenges
    async def get_challenges(self) -> Dict[str, Any]:
        """Get all challenges."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/challenges",
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
    
    async def create_challenge(self, challenge_data: CreateChallengeRequest) -> Dict[str, Any]:
        """Create a new challenge."""
        if not self.base_url:
            return {"error": "API service URL not configured"}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/challenges",
                    json=challenge_data.dict(),
                    headers=self._get_headers()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}

# Create a global API service instance
api_service = ScaffoldApiService() 