"""Main agent system for Pili fitness chatbot using LangGraph patterns."""

import uuid
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool, create_swarm
from typing import Dict, Any, List, Optional
import json

from .prompts import logger_prompt, coach_prompt
from .utils import get_mcp_tools, execute_mcp_tool, extract_user_id_from_args, print_stream
from config.settings import settings, get_configuration


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


def create_mcp_tool_function(tool_name: str, tool_description: str, user_id: str):
    """Create a proper function wrapper for MCP tools compatible with LangGraph."""
    
    async def mcp_tool_func(**kwargs) -> str:
        """Execute the MCP tool with given arguments."""
        # Ensure user_id is in arguments
        kwargs = extract_user_id_from_args(kwargs, user_id)
        return await execute_mcp_tool(tool_name, kwargs)
    
    # Set function attributes for LangGraph compatibility
    mcp_tool_func.__name__ = tool_name
    mcp_tool_func.__doc__ = tool_description
    mcp_tool_func.name = tool_name
    mcp_tool_func.description = tool_description
    
    return mcp_tool_func


async def create_mcp_tools_for_agent(user_id: str) -> List:
    """Create MCP tools for use with LangGraph agents."""
    available_tools = await get_mcp_tools()
    
    mcp_tools = []
    for tool in available_tools:
        if isinstance(tool, dict) and tool.get("name"):
            mcp_tool_func = create_mcp_tool_function(
                tool_name=tool.get("name", ""),
                tool_description=tool.get("description", ""),
                user_id=user_id
            )
            mcp_tools.append(mcp_tool_func)
    
    return mcp_tools


async def create_logger_agent(user_id: str):
    """Create the logger agent with dynamic MCP tools."""
    mcp_tools = await create_mcp_tools_for_agent(user_id)
    
    # Add handoff tool to coach agent
    all_tools = mcp_tools + [transfer_to_coach_agent]
    
    logger_agent = create_react_agent(
        model,
        prompt=logger_prompt,
        tools=all_tools,
        name="logger_agent",
    )
    
    return logger_agent


async def create_coach_agent(user_id: str):
    """Create the coach agent with dynamic MCP tools."""
    mcp_tools = await create_mcp_tools_for_agent(user_id)
    
    # Add handoff tool to logger agent  
    all_tools = mcp_tools + [transfer_to_logger_agent]
    
    coach_agent = create_react_agent(
        model,
        prompt=coach_prompt,
        tools=all_tools,
        name="coach_agent",
    )
    
    return coach_agent


async def create_agent_swarm(user_id: str):
    """Create the agent swarm for the given user."""
    logger_agent = await create_logger_agent(user_id)
    coach_agent = await create_coach_agent(user_id)
    
    # Create swarm with logger as default (handles most basic requests)
    agent_swarm = create_swarm(
        [logger_agent, coach_agent], 
        default_active_agent="logger_agent"
    )
    
    return agent_swarm.compile()


class PiliAgentSystem:
    """Main agent system for Pili fitness chatbot."""
    
    def __init__(self):
        self.agent_cache = {}  # Cache compiled agents per user
        self.max_cache_size = 100  # Limit cache size
    
    async def get_agent_for_user(self, user_id: str):
        """Get or create agent system for a specific user."""
        if user_id not in self.agent_cache:
            # Create new agent system for user
            if len(self.agent_cache) >= self.max_cache_size:
                # Remove oldest entry if cache is full
                oldest_user = next(iter(self.agent_cache))
                del self.agent_cache[oldest_user]
            
            self.agent_cache[user_id] = await create_agent_swarm(user_id)
        
        return self.agent_cache[user_id]
    
    async def process_request(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process a user request through the agent system."""
        try:
            # Get agent system for user
            agent_app = await self.get_agent_for_user(user_id)
            
            # Prepare initial state
            initial_state = {
                "messages": [{"role": "user", "content": message}]
            }
            
            # Run the agent system
            result = await agent_app.ainvoke(initial_state)
            
            config = {"configurable": {"thread_id": str(uuid.uuid4()) + user_id, "user_id": user_id}}
            print_stream(agent_app.stream(initial_state, config=config, subgraphs=True))

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
                "chain_of_thought": [f"Processed request through LangGraph agent swarm"]
            }
            
        except Exception as e:
            print(f"Error in agent system: {e}")
            return {
                "response": "I'm sorry, something went wrong. Please try again! 💪",
                "logs": [{"error": str(e), "agent_system": "failed"}],
                "chain_of_thought": [f"Error occurred: {str(e)}"]
            }
    
    def clear_user_cache(self, user_id: str):
        """Clear cached agent for a specific user."""
        if user_id in self.agent_cache:
            del self.agent_cache[user_id]
    
    def clear_all_cache(self):
        """Clear all cached agents."""
        self.agent_cache.clear()


# Global agent system instance
agent_system = PiliAgentSystem() 