"""Main agent system for Pili fitness chatbot using LangGraph patterns."""

import uuid
from datetime import datetime
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool, create_swarm
from typing import Dict, Any, List, Optional, Tuple
import json

# Fix LangChain compatibility issues
try:
    import langchain
    if not hasattr(langchain, 'verbose'):
        langchain.verbose = False
    if not hasattr(langchain, 'debug'):
        langchain.debug = False
    if not hasattr(langchain, 'llm_cache'):
        langchain.llm_cache = None
except ImportError:
    pass

from .prompts import create_logger_prompt, create_coach_prompt
from .utils import print_stream
from services.mcp_client import create_mcp_client
from config.settings import settings, get_configuration


def format_user_message_with_context(user_id: str, message: str) -> str:
    """Add datetime and user context to the beginning of user message for better LLM understanding."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[Time: {current_time}][UserId: {user_id}] {message}"


# Initialize LLM based on configuration
config = get_configuration()

if config.llm_provider == "openai":
    # Use OpenAI API
    openai_client = OpenAI(api_key=config.openai_api_key)
    model = ChatOpenAI(
        model=config.openai_model,
        api_key=config.openai_api_key,
        temperature=0.7
    )
else:
    # Use local LLM (vLLM, Ollama, etc.) with OpenAI-compatible interface
    openai_client = OpenAI(
        base_url=config.local_llm_base_url,
        api_key=config.local_llm_api_key or "dummy-key"
    )
    model = ChatOpenAI(
        model=config.local_llm_model,
        base_url=config.local_llm_base_url,
        api_key=config.local_llm_api_key or "dummy-key",
        temperature=0.7
    )


# Create handoff tools for agent communication
transfer_to_logger_agent = create_handoff_tool(
    agent_name="logger_agent",
    description="Transfer to the logger agent for activity logging, club management, and basic data retrieval from Scaffold Your Shape system."
)

transfer_to_coach_agent = create_handoff_tool(
    agent_name="coach_agent", 
    description="Transfer to the coach agent for workout planning, progress analysis, and personalized coaching advice."
)


async def create_mcp_tools_for_agent(mcp_client, user_id: str) -> List:
    """Create MCP tools for use with LangGraph agents using an existing client."""
    # Get tools using the provided MCP client (don't close it!)
    tools = await mcp_client.get_tools(user_id)
    return tools


async def create_logger_agent(mcp_client, user_id: str):
    """Create the logger agent with dynamic MCP tools and user-specific prompt."""
    mcp_tools = await create_mcp_tools_for_agent(mcp_client, user_id)
    
    # Add handoff tool to coach agent
    all_tools = mcp_tools + [transfer_to_coach_agent]
    
    # Create user-specific prompt
    logger_prompt = create_logger_prompt(user_id)
    
    logger_agent = create_react_agent(
        model,
        prompt=logger_prompt,
        tools=all_tools,
        name="logger_agent",
    )
    
    return logger_agent


async def create_coach_agent(mcp_client, user_id: str):
    """Create the coach agent with dynamic MCP tools and user-specific prompt."""
    mcp_tools = await create_mcp_tools_for_agent(mcp_client, user_id)
    
    # Add handoff tool to logger agent  
    all_tools = mcp_tools + [transfer_to_logger_agent]
    
    # Create user-specific prompt
    coach_prompt = create_coach_prompt(user_id)
    
    coach_agent = create_react_agent(
        model,
        prompt=coach_prompt,
        tools=all_tools,
        name="coach_agent",
    )
    
    return coach_agent


async def create_agent_swarm(user_id: str) -> Tuple[Any, Any]:
    """Create the agent swarm for the given user and return (agent_app, mcp_client)."""
    # Create MCP client for this user
    mcp_client = create_mcp_client()
    
    try:
        logger_agent = await create_logger_agent(mcp_client, user_id)
        coach_agent = await create_coach_agent(mcp_client, user_id)
        
        # Create swarm with logger as default (handles most basic requests)
        agent_swarm = create_swarm(
            [logger_agent, coach_agent], 
            default_active_agent="logger_agent"
        )
        
        agent_app = agent_swarm.compile()
        return agent_app, mcp_client
        
    except Exception as e:
        # If creation fails, close the client
        await mcp_client.close()
        raise e


class PiliAgentSystem:
    """Main agent system for Pili fitness chatbot."""
    
    def __init__(self):
        self.agent_cache = {}  # Cache compiled agents and their MCP clients per user
        self.max_cache_size = 100  # Limit cache size
    
    async def get_agent_for_user(self, user_id: str):
        """Get or create agent system for a specific user."""
        if user_id not in self.agent_cache:
            # Create new agent system for user
            if len(self.agent_cache) >= self.max_cache_size:
                # Remove oldest entry if cache is full and close its MCP client
                oldest_user = next(iter(self.agent_cache))
                old_entry = self.agent_cache[oldest_user]
                if old_entry and len(old_entry) > 1:
                    old_mcp_client = old_entry[1]
                    try:
                        await old_mcp_client.close()
                    except Exception as e:
                        print(f"Error closing old MCP client for user {oldest_user}: {e}")
                del self.agent_cache[oldest_user]
            
            # Create new agent system with MCP client
            agent_app, mcp_client = await create_agent_swarm(user_id)
            self.agent_cache[user_id] = (agent_app, mcp_client)
        
        return self.agent_cache[user_id][0]  # Return just the agent app
    
    async def process_request(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process a user request through the agent system."""
        try:
            # Get agent system for user
            agent_app = await self.get_agent_for_user(user_id)
            
            # Format user message with datetime and user context for better LLM understanding
            formatted_message = format_user_message_with_context(user_id, message)
            
            # Prepare initial state with user context
            initial_state = {
                "messages": [{"role": "user", "content": formatted_message}],
                "user_id": user_id  # Include user_id in state
            }
            
            # Run the agent system with user-specific configuration
            config = {
                "configurable": {
                    "thread_id": f"{user_id}_{uuid.uuid4()}", 
                    "user_id": user_id
                }
            }
            
            result = await agent_app.ainvoke(initial_state, config=config)
            
            # Extract the final response
            messages = result.get("messages", [])
            if messages:
                final_message = messages[-1]
                response = final_message.content if hasattr(final_message, 'content') else str(final_message)
            else:
                response = "I'm sorry, I couldn't process your request right now."
            
            # Prepare logs for debugging
            logs = [{
                "agent_system": "langgraph_swarm",
                "user_id": user_id,
                "message_count": len(messages),
                "final_response": response
            }]
            
            return {
                "response": response,
                "logs": logs,
                "chain_of_thought": [f"Processed request for user {user_id} through LangGraph agent swarm"]
            }
            
        except Exception as e:
            print(f"Error in agent system for user {user_id}: {e}")
            return {
                "response": "I'm sorry, something went wrong. Please try again! 💪",
                "logs": [{"error": str(e), "agent_system": "failed", "user_id": user_id}],
                "chain_of_thought": [f"Error occurred for user {user_id}: {str(e)}"]
            }
    
    async def clear_user_cache(self, user_id: str):
        """Clear cached agent for a specific user and close its MCP client."""
        if user_id in self.agent_cache:
            entry = self.agent_cache[user_id]
            if entry and len(entry) > 1:
                mcp_client = entry[1]
                try:
                    await mcp_client.close()
                except Exception as e:
                    print(f"Error closing MCP client for user {user_id}: {e}")
            del self.agent_cache[user_id]
    
    async def clear_all_cache(self):
        """Clear all cached agents and close all MCP clients."""
        for user_id, entry in self.agent_cache.items():
            if entry and len(entry) > 1:
                mcp_client = entry[1]
                try:
                    await mcp_client.close()
                except Exception as e:
                    print(f"Error closing MCP client for user {user_id}: {e}")
        self.agent_cache.clear()


# Global agent system instance
agent_system = PiliAgentSystem() 