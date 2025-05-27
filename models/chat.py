from pydantic import BaseModel
from typing import List, Dict, Any

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    logs: List[Dict[str, Any]] = []
    
class ExerciseLog(BaseModel):
    user_id: str
    exercise_type: str
    duration: int = 0
    repetitions: int = 0
    description: str = ""
    
class ClubAction(BaseModel):
    user_id: str
    club_id: str
    action: str  # "join" or "exit" 