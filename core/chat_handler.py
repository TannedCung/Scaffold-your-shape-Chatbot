from typing import Dict, Any
from models.chat import ChatRequest, ChatResponse
from agents.exercise_agent import exercise_agent, ExerciseAgentState

class ChatHandler:
    def __init__(self):
        self.agent = exercise_agent
        
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request using the exercise agent."""
        
        # Create initial state
        state = ExerciseAgentState()
        state.user_id = request.user_id
        state.message = request.message
        
        # Run the agent workflow
        result = await self.agent.ainvoke(state)
        
        # Extract response and logs
        response = result.response if hasattr(result, 'response') else "I'm sorry, something went wrong."
        logs = result.logs if hasattr(result, 'logs') else []
        
        return ChatResponse(response=response, logs=logs)

# Create a global chat handler instance
chat_handler = ChatHandler() 