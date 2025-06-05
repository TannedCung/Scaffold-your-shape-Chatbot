from typing import Dict, Any
from models.chat import ChatRequest, ChatResponse
from agents.pili_agent import pili_agent

class ChatHandler:
    def __init__(self):
        self.agent = pili_agent
        
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request using the Pili agent with LLM integration."""
        
        # Create initial state as dictionary
        state = {
            "user_id": request.user_id,
            "message": request.message,
            "intent": "",
            "confidence": 0.0,
            "extracted_info": {},
            "action_result": "",
            "thinking_process": "",
            "response": "",
            "logs": []
        }
        
        # Run the agent workflow
        result = await self.agent.ainvoke(state)
        
        # Extract response and logs
        response = result.get("response", "I'm sorry, something went wrong.")
        logs = result.get("logs", [])
        
        # Add metadata to logs
        logs.append({
            "intent": result.get("intent", "unknown"),
            "confidence": result.get("confidence", 0.0),
            "extracted_info": result.get("extracted_info", {}),
            "action_result": result.get("action_result", ""),
            "llm_provider": "current"  # Can be enhanced to show actual provider
        })
        
        return ChatResponse(response=response, logs=logs)

# Create a global chat handler instance
chat_handler = ChatHandler() 