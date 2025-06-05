from typing import Dict, Any
from models.chat import ChatRequest, ChatResponse
from agents.pili_agent import pili_agent
from services.llm_service import llm_service
from tools.api_tools import (
    log_activity_tool, 
    get_user_activities_tool,
    manage_club_tool,
    manage_challenge_tool,
    get_user_stats_tool
)

class ChatHandler:
    def __init__(self):
        self.agent = pili_agent
        
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request using simplified logic for debugging."""
        
        try:
            # Step 1: Detect intent
            intent_result = await llm_service.detect_intent(request.message)
            intent = intent_result.get("intent", "unknown")
            confidence = intent_result.get("confidence", 0.5)
            extracted_info = intent_result.get("extracted_info", {})
            
            # Step 2: Handle the intent
            action_result = ""
            if intent == "log_activity":
                action_result = await log_activity_tool(request.user_id, request.message)
            elif intent == "manage_clubs":
                action_result = await manage_club_tool(request.user_id, request.message)
            elif intent == "manage_challenges":
                action_result = await manage_challenge_tool(request.user_id, request.message)
            elif intent == "get_stats":
                action_result = await get_user_stats_tool(request.user_id)
            elif intent == "help":
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
            else:
                action_result = (
                    "I'm Pili, and I didn't quite catch that! 🤔 I can help you with:\n"
                    "• Logging workouts and activities\n"
                    "• Finding and creating fitness clubs\n"
                    "• Managing fitness challenges\n"
                    "• Tracking your progress\n\n"
                    "Try saying something like 'I ran 3 miles' or 'Show my stats' or just type 'help' for more examples!"
                )
            
            # Step 3: Generate final response using LLM (with fallback)
            try:
                final_response = await llm_service.generate_response(intent, request.message, action_result)
            except Exception as e:
                print(f"LLM response generation failed: {e}")
                final_response = action_result
            
            # Create logs
            logs = [{
                "intent": intent,
                "confidence": confidence,
                "extracted_info": extracted_info,
                "action_result": action_result,
                "llm_provider": llm_service.provider
            }]
            
            return ChatResponse(response=final_response, logs=logs)
            
        except Exception as e:
            print(f"Chat processing error: {e}")
            return ChatResponse(
                response="I'm sorry, something went wrong. Please try again.",
                logs=[{"error": str(e)}]
            )

# Create a global chat handler instance
chat_handler = ChatHandler() 