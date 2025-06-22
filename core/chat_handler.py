from typing import Dict, Any
from models.chat import ChatRequest, ChatResponse
from agents.orchestration_agent import orchestration_agent

class ChatHandler:
    def __init__(self):
        self.orchestration_agent = orchestration_agent
        
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request using the orchestration agent."""
        
        try:
            # Use orchestration agent to handle the request
            result = await self.orchestration_agent.process_request(
                request.user_id, 
                request.message
            )
            
            return ChatResponse(
                response=result["response"],
                logs=result["logs"]
            )
            
        except Exception as e:
            print(f"Chat processing error: {e}")
            return ChatResponse(
                response="I'm sorry, something went wrong. Please try again.",
                logs=[{"error": str(e), "orchestration_agent": "failed"}]
            )

# Create a global chat handler instance
chat_handler = ChatHandler() 