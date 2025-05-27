from typing import Dict, Any
from langgraph import StateGraph, END
from langsmith import Client
from tools.exercise_tools import (
    log_exercise_tool, 
    join_club_tool, 
    get_progress_tool, 
    extract_club_info
)
from config.settings import settings

# Initialize LangSmith client
client = Client()

class ExerciseAgentState:
    def __init__(self):
        self.user_id: str = ""
        self.message: str = ""
        self.intent: str = ""
        self.response: str = ""
        self.logs: list = []

def detect_intent(state: ExerciseAgentState) -> str:
    """Detect the intent from the user message."""
    message = state.message.lower()
    
    if any(word in message for word in ["log", "did", "completed", "finished"]):
        state.intent = "log_exercise"
    elif any(word in message for word in ["join", "exit", "leave", "club", "challenge"]):
        state.intent = "club_action"
    elif any(word in message for word in ["progress", "stats", "history", "show"]):
        state.intent = "get_progress"
    elif "help" in message:
        state.intent = "help"
    else:
        state.intent = "unknown"
    
    return state.intent

async def handle_log_exercise(state: ExerciseAgentState) -> ExerciseAgentState:
    """Handle exercise logging."""
    response = await log_exercise_tool(state.user_id, state.message)
    state.response = response
    return state

async def handle_club_action(state: ExerciseAgentState) -> ExerciseAgentState:
    """Handle club join/exit actions."""
    club_info = extract_club_info(state.message)
    
    if club_info["action"] == "unknown":
        state.response = "I didn't understand the club action. Please specify 'join' or 'exit/leave'."
    else:
        response = await join_club_tool(
            state.user_id, 
            club_info["club_id"], 
            club_info["action"]
        )
        state.response = response
    
    return state

async def handle_get_progress(state: ExerciseAgentState) -> ExerciseAgentState:
    """Handle progress requests."""
    progress_data = await get_progress_tool(state.user_id)
    
    if "error" in progress_data:
        state.response = f"Failed to get progress: {progress_data['error']}"
    elif progress_data.get("status") == "no_external_service":
        state.response = "Progress tracking is not available without external service configuration."
    else:
        # Format progress data
        if progress_data.get("progress"):
            state.response = f"Here's your progress: {len(progress_data['progress'])} activities logged."
            state.logs = progress_data["progress"]
        else:
            state.response = "No exercise history found."
    
    return state

def handle_help(state: ExerciseAgentState) -> ExerciseAgentState:
    """Handle help requests."""
    state.response = (
        "I can help you with:\n"
        "• Log exercises: 'I did 20 pushups'\n"
        "• Track progress: 'Show my progress'\n"
        "• Join clubs: 'Join club fitness'\n"
        "• Exit clubs: 'Leave club fitness'"
    )
    return state

def handle_unknown(state: ExerciseAgentState) -> ExerciseAgentState:
    """Handle unknown intents."""
    state.response = "I didn't understand that. Type 'help' to see what I can do!"
    return state

def create_exercise_agent():
    """Create the LangGraph exercise agent."""
    
    # Create the state graph
    workflow = StateGraph(ExerciseAgentState)
    
    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("log_exercise", handle_log_exercise)
    workflow.add_node("club_action", handle_club_action)
    workflow.add_node("get_progress", handle_get_progress)
    workflow.add_node("help", handle_help)
    workflow.add_node("unknown", handle_unknown)
    
    # Add edges
    workflow.set_entry_point("detect_intent")
    
    workflow.add_conditional_edges(
        "detect_intent",
        lambda state: state.intent,
        {
            "log_exercise": "log_exercise",
            "club_action": "club_action", 
            "get_progress": "get_progress",
            "help": "help",
            "unknown": "unknown"
        }
    )
    
    # All handler nodes go to END
    for node in ["log_exercise", "club_action", "get_progress", "help", "unknown"]:
        workflow.add_edge(node, END)
    
    return workflow.compile()

# Create the agent instance
exercise_agent = create_exercise_agent() 