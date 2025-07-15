from typing import Dict, Any
from models.chat import ChatRequest, ChatResponse
from agents.agent import agent_system


class ChatHandler:
    """Chat handler using the refactored LangGraph agent system."""
    
    def __init__(self):
        self.agent_system = agent_system
        
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request using the LangGraph agent system."""
        
        try:
            # Use the new agent system to handle the request
            result = await self.agent_system.process_request(
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
                response="I'm sorry, something went wrong. Please try again! 💪",
                logs=[{"error": str(e), "agent_system": "langgraph_swarm", "status": "failed"}]
            )


# Create a global chat handler instance
chat_handler = ChatHandler() 