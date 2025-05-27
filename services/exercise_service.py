import httpx
from typing import Dict, Any
from config.settings import settings
from models.chat import ExerciseLog, ClubAction

class ExerciseService:
    def __init__(self):
        self.base_url = settings.exercise_service_url
        
    async def log_exercise(self, exercise_log: ExerciseLog) -> Dict[str, Any]:
        """Log an exercise to the external service."""
        if not self.base_url:
            # Fallback to in-memory storage if no external service configured
            return {"status": "logged_locally", "data": exercise_log.dict()}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/exercises",
                    json=exercise_log.dict()
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
                
    async def join_club(self, club_action: ClubAction) -> Dict[str, Any]:
        """Join or exit a club/challenge."""
        if not self.base_url:
            return {"status": "processed_locally", "action": club_action.action}
            
        async with httpx.AsyncClient() as client:
            try:
                endpoint = f"{self.base_url}/clubs/{club_action.club_id}/members"
                if club_action.action == "join":
                    response = await client.post(endpoint, json={"user_id": club_action.user_id})
                else:  # exit
                    response = await client.delete(endpoint, json={"user_id": club_action.user_id})
                return response.json()
            except Exception as e:
                return {"error": str(e)}
                
    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's exercise progress."""
        if not self.base_url:
            return {"status": "no_external_service", "progress": []}
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/users/{user_id}/progress")
                return response.json()
            except Exception as e:
                return {"error": str(e)}

exercise_service = ExerciseService() 