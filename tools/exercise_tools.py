import re
from typing import Dict, Any
from models.chat import ExerciseLog, ClubAction
from services.exercise_service import exercise_service

def extract_exercise_info(message: str) -> Dict[str, Any]:
    """Extract exercise information from user message."""
    message = message.lower()
    
    # Extract numbers for repetitions/duration
    numbers = re.findall(r'\d+', message)
    
    # Extract exercise type
    exercise_types = {
        'pushup': ['pushup', 'push-up', 'push up'],
        'squat': ['squat', 'squats'],
        'run': ['run', 'running', 'jog', 'jogging'],
        'walk': ['walk', 'walking'],
        'bike': ['bike', 'biking', 'cycling'],
        'swim': ['swim', 'swimming'],
        'yoga': ['yoga'],
        'weightlifting': ['weights', 'lifting', 'bench']
    }
    
    detected_exercise = "general"
    for exercise, keywords in exercise_types.items():
        if any(keyword in message for keyword in keywords):
            detected_exercise = exercise
            break
    
    reps = int(numbers[0]) if numbers else 0
    duration = int(numbers[1]) if len(numbers) > 1 else 0
    
    return {
        "exercise_type": detected_exercise,
        "repetitions": reps,
        "duration": duration,
        "description": message
    }

async def log_exercise_tool(user_id: str, message: str) -> str:
    """Tool to log an exercise."""
    exercise_info = extract_exercise_info(message)
    exercise_log = ExerciseLog(
        user_id=user_id,
        **exercise_info
    )
    
    result = await exercise_service.log_exercise(exercise_log)
    
    if "error" in result:
        return f"Failed to log exercise: {result['error']}"
    
    return f"Exercise logged successfully! {exercise_info['exercise_type']} - {exercise_info['repetitions']} reps"

async def join_club_tool(user_id: str, club_id: str, action: str) -> str:
    """Tool to join or exit a club/challenge."""
    club_action = ClubAction(
        user_id=user_id,
        club_id=club_id,
        action=action
    )
    
    result = await exercise_service.join_club(club_action)
    
    if "error" in result:
        return f"Failed to {action} club: {result['error']}"
    
    return f"Successfully {action}ed club {club_id}!"

async def get_progress_tool(user_id: str) -> Dict[str, Any]:
    """Tool to get user's exercise progress."""
    result = await exercise_service.get_user_progress(user_id)
    return result

def extract_club_info(message: str) -> Dict[str, str]:
    """Extract club information from user message."""
    message = message.lower()
    
    # Simple pattern matching for club actions
    if "join" in message:
        action = "join"
    elif "exit" in message or "leave" in message:
        action = "exit"
    else:
        action = "unknown"
    
    # Extract club ID (simple pattern)
    club_match = re.search(r'club\s+(\w+)', message)
    club_id = club_match.group(1) if club_match else "default"
    
    return {"action": action, "club_id": club_id} 