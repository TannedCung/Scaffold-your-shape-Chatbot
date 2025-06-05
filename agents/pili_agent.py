from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langsmith import Client
from tools.api_tools import (
    log_activity_tool, 
    get_user_activities_tool,
    manage_club_tool,
    manage_challenge_tool,
    get_user_stats_tool
)
from config.settings import settings

# Initialize LangSmith client
client = Client()

class PiliAgentState(TypedDict):
    user_id: str
    message: str
    intent: str
    response: str
    logs: list

def detect_intent(state: PiliAgentState) -> PiliAgentState:
    """Detect the intent from the user message."""
    message = state["message"].lower()
    
    # Activity logging intents
    if any(word in message for word in ["did", "completed", "finished", "ran", "cycled", "swam", "walked", "workout"]):
        state["intent"] = "log_activity"
    
    # Club management intents
    elif any(word in message for word in ["club", "join club", "create club", "clubs"]):
        state["intent"] = "manage_clubs"
    
    # Challenge management intents
    elif any(word in message for word in ["challenge", "challenges", "create challenge", "join challenge"]):
        state["intent"] = "manage_challenges"
    
    # Stats and progress intents
    elif any(word in message for word in ["stats", "statistics", "progress", "summary", "activities", "history"]):
        state["intent"] = "get_stats"
    
    # Help intent
    elif any(word in message for word in ["help", "what can you do", "commands"]):
        state["intent"] = "help"
    
    else:
        state["intent"] = "unknown"
    
    return state

async def handle_log_activity(state: PiliAgentState) -> PiliAgentState:
    """Handle activity logging."""
    response = await log_activity_tool(state["user_id"], state["message"])
    state["response"] = response
    return state

async def handle_manage_clubs(state: PiliAgentState) -> PiliAgentState:
    """Handle club management (create, join, search)."""
    response = await manage_club_tool(state["user_id"], state["message"])
    state["response"] = response
    return state

async def handle_manage_challenges(state: PiliAgentState) -> PiliAgentState:
    """Handle challenge management (create, join, search)."""
    response = await manage_challenge_tool(state["user_id"], state["message"])
    state["response"] = response
    return state

async def handle_get_stats(state: PiliAgentState) -> PiliAgentState:
    """Handle stats and progress requests."""
    response = await get_user_stats_tool(state["user_id"])
    state["response"] = response
    return state

def handle_help(state: PiliAgentState) -> PiliAgentState:
    """Handle help requests."""
    state["response"] = (
        "Hi! I'm Pili, your fitness companion! 🏃‍♀️ Here's what I can help you with:\n\n"
        "📝 **Log Activities:**\n"
        "• 'I ran 5 km in 30 minutes'\n"
        "• 'Did 45 minutes of yoga'\n"
        "• 'Cycled 15 km at the park'\n\n"
        "👥 **Club Management:**\n"
        "• 'Show me clubs' or 'Find running clubs'\n"
        "• 'Create club runners for people who love running'\n\n"
        "🏆 **Challenges:**\n"
        "• 'Show challenges' or 'Find running challenges'\n"
        "• 'Create marathon challenge for 42 km'\n\n"
        "📊 **Track Progress:**\n"
        "• 'Show my stats' or 'My progress'\n"
        "• 'How many activities have I logged?'\n\n"
        "Just tell me what you want to do in natural language!"
    )
    return state

def handle_unknown(state: PiliAgentState) -> PiliAgentState:
    """Handle unknown intents."""
    state["response"] = (
        "I'm Pili, and I didn't quite catch that! 🤔 I can help you with:\n"
        "• Logging workouts and activities\n"
        "• Finding and creating fitness clubs\n"
        "• Managing fitness challenges\n"
        "• Tracking your progress\n\n"
        "Try saying something like 'I ran 3 miles' or 'Show my stats' or just type 'help' for more examples!"
    )
    return state

def create_pili_agent():
    """Create the LangGraph Pili agent."""
    
    # Create the state graph
    workflow = StateGraph(PiliAgentState)
    
    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("log_activity", handle_log_activity)
    workflow.add_node("manage_clubs", handle_manage_clubs)
    workflow.add_node("manage_challenges", handle_manage_challenges)
    workflow.add_node("get_stats", handle_get_stats)
    workflow.add_node("help", handle_help)
    workflow.add_node("unknown", handle_unknown)
    
    # Add edges
    workflow.set_entry_point("detect_intent")
    
    workflow.add_conditional_edges(
        "detect_intent",
        lambda state: state["intent"],
        {
            "log_activity": "log_activity",
            "manage_clubs": "manage_clubs",
            "manage_challenges": "manage_challenges",
            "get_stats": "get_stats",
            "help": "help",
            "unknown": "unknown"
        }
    )
    
    # All handler nodes go to END
    for node in ["log_activity", "manage_clubs", "manage_challenges", "get_stats", "help", "unknown"]:
        workflow.add_edge(node, END)
    
    return workflow.compile()

# Create the agent instance
pili_agent = create_pili_agent() 