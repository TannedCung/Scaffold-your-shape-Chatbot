from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    user_id: str
    message: str
    stream: Optional[bool] = False  # Add streaming support

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

class StreamChunk(BaseModel):
    """Model for streaming response chunks."""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str = "pili"
    choices: List[Dict[str, Any]]
    
class StreamChoice(BaseModel):
    """Model for streaming choice data."""
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None 