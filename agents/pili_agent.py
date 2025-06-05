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
from services.llm_service import llm_service
from config.settings import settings

# Initialize LangSmith client
client = Client()

class PiliAgentState(TypedDict):
    user_id: str
    message: str
    intent: str
    confidence: float
    extracted_info: dict
    action_result: str
    thinking_process: str
    response: str
    logs: list

async def detect_intent(state: PiliAgentState) -> PiliAgentState:
    """Detect the intent from the user message using LLM."""
    try:
        intent_result = await llm_service.detect_intent(state["message"])
        
        state["intent"] = intent_result.get("intent", "unknown")
        state["confidence"] = intent_result.get("confidence", 0.5)
        state["extracted_info"] = intent_result.get("extracted_info", {})
    except Exception as e:
        print(f"Error in detect_intent: {e}")
        # Fallback to rule-based detection
        fallback_result = llm_service._fallback_intent_detection(state["message"])
        state["intent"] = fallback_result.get("intent", "unknown")
        state["confidence"] = fallback_result.get("confidence", 0.5)
        state["extracted_info"] = fallback_result.get("extracted_info", {})
    
    return state

async def handle_log_activity(state: PiliAgentState) -> PiliAgentState:
    """Handle activity logging."""
    action_result = await log_activity_tool(state["user_id"], state["message"])
    state["action_result"] = action_result
    return state

async def handle_manage_clubs(state: PiliAgentState) -> PiliAgentState:
    """Handle club management (create, join, search)."""
    action_result = await manage_club_tool(state["user_id"], state["message"])
    state["action_result"] = action_result
    return state

async def handle_manage_challenges(state: PiliAgentState) -> PiliAgentState:
    """Handle challenge management (create, join, search)."""
    action_result = await manage_challenge_tool(state["user_id"], state["message"])
    state["action_result"] = action_result
    return state

async def handle_get_stats(state: PiliAgentState) -> PiliAgentState:
    """Handle stats and progress requests."""
    action_result = await get_user_stats_tool(state["user_id"])
    state["action_result"] = action_result
    return state

async def handle_help(state: PiliAgentState) -> PiliAgentState:
    """Handle help requests."""
    action_result = (
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
    state["action_result"] = action_result
    return state

async def handle_unknown(state: PiliAgentState) -> PiliAgentState:
    """Handle unknown intents."""
    action_result = (
        "I'm Pili, and I didn't quite catch that! 🤔 I can help you with:\n"
        "• Logging workouts and activities\n"
        "• Finding and creating fitness clubs\n"
        "• Managing fitness challenges\n"
        "• Tracking your progress\n\n"
        "Try saying something like 'I ran 3 miles' or 'Show my stats' or just type 'help' for more examples!"
    )
    state["action_result"] = action_result
    return state

async def generate_response(state: PiliAgentState) -> PiliAgentState:
    """Generate final response using LLM."""
    try:
        # Generate response using LLM
        full_response = await llm_service.generate_response(
            state["intent"], 
            state["message"], 
            state["action_result"]
        )
        
        # Extract thinking process and final response
        thinking, final_response = llm_service.extract_thinking_process(full_response)
        
        state["thinking_process"] = thinking
        state["response"] = final_response
    except Exception as e:
        print(f"Error in generate_response: {e}")
        # Fallback to action result if LLM fails
        state["thinking_process"] = ""
        state["response"] = state.get("action_result", "I'm sorry, something went wrong.")
    
    return state

def create_pili_agent():
    """Create the LangGraph Pili agent with LLM integration."""
    
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
    workflow.add_node("generate_response", generate_response)
    
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
    
    # All handler nodes go to generate_response
    for node in ["log_activity", "manage_clubs", "manage_challenges", "get_stats", "help", "unknown"]:
        workflow.add_edge(node, "generate_response")
    
    # generate_response goes to END
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()

# Create the agent instance
pili_agent = create_pili_agent() 