"""Main agent system for Pili fitness chatbot using LangGraph patterns."""

import uuid
from datetime import datetime
import langchain_core

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool, create_swarm
# Removed unused imports - using custom react agent directly
from typing import Dict, Any, List, Optional, Tuple
import json
from langsmith import traceable

# Fix langchain globals issue - add missing attributes for compatibility
import os
import langchain

# Set environment variables to control LangChain behavior
os.environ['LANGCHAIN_DEBUG'] = 'false'

# Fix compatibility issue - add missing debug attributes
if not hasattr(langchain, 'debug'):
    langchain.debug = False
if not hasattr(langchain, 'verbose'):
    langchain.verbose = False
if not hasattr(langchain, 'llm_cache'):
    langchain.llm_cache = None

# Note: These attributes are deprecated but needed for compatibility

# Initialize tracing service
from services.tracing_service import initialize_tracing, is_tracing_enabled, create_run_metadata
initialize_tracing()


from .prompts import create_logger_prompt, create_coach_prompt, orchestration_prompt
from .utils import print_stream
from services.mcp_client import create_mcp_client
from services.langchain_memory_service import langchain_memory_service
from models.memory import MemoryConfiguration
from config.settings import settings, get_configuration


def format_user_message_with_context(user_id: str, message: str) -> str:
    """Add datetime and user context to the beginning of user message for better LLM understanding."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[Time: {current_time}][UserId: {user_id}] {message}"


# Note: OrchestrationState no longer needed since we use custom react agent directly


# Initialize LLM based on configuration
config = get_configuration()

def get_model():
    """Get the LLM model with lazy initialization to avoid import-time errors."""
    config = get_configuration()
    
    if config.llm_provider == "openai":
        # Use OpenAI API
        return ChatOpenAI(
            model=config.openai_model,
            api_key=config.openai_api_key,
            temperature=0.7,
            verbose=False,
            streaming=False
        )
    else:
        # Use local LLM (vLLM, Ollama, etc.) with OpenAI-compatible interface
        return ChatOpenAI(
            model=config.local_llm_model,
            base_url=config.local_llm_base_url,
            api_key=config.local_llm_api_key or "dummy-key",
            temperature=0.7,
            verbose=False,
            streaming=False
        )

def get_openai_client():
    """Get the OpenAI client with lazy initialization."""
    config = get_configuration()
    
    if config.llm_provider == "openai":
        return OpenAI(api_key=config.openai_api_key)
    else:
        return OpenAI(
            base_url=config.local_llm_base_url,
            api_key=config.local_llm_api_key or "dummy-key"
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

# Create a handoff tool that routes to complete response node
transfer_to_complete_response = create_handoff_tool(
    agent_name="complete_response_node",
    description="Complete the conversation with a final response after task completion."
)

transfer_to_orchestration_agent = create_handoff_tool(
    agent_name="orchestration_agent",
    description="Transfer back to the orchestration agent for routing decisions, handling new queries, or when the current task is complete."
)


async def create_mcp_tools_for_agent(mcp_client, user_id: str) -> List:
    """Create MCP tools for use with LangGraph agents using an existing client."""
    # Get tools using the provided MCP client (don't close it!)
    tools = await mcp_client.get_tools(user_id)
    return tools


async def create_logger_agent(mcp_client, user_id: str):
    """Create the logger agent with dynamic MCP tools and user-specific prompt."""
    mcp_tools = await create_mcp_tools_for_agent(mcp_client, user_id)
    
    # Add handoff tools to coach and complete response
    all_tools = mcp_tools + [transfer_to_coach_agent, transfer_to_complete_response]
    
    # Create user-specific prompt
    logger_prompt = create_logger_prompt(user_id)
    
    logger_agent = create_react_agent(
        get_model(),
        prompt=logger_prompt,
        tools=all_tools,
        name="logger_agent",
    )
    
    return logger_agent


async def create_coach_agent(mcp_client, user_id: str):
    """Create the coach agent with dynamic MCP tools and user-specific prompt."""
    mcp_tools = await create_mcp_tools_for_agent(mcp_client, user_id)
    
    # Add handoff tools to logger and complete response
    all_tools = mcp_tools + [transfer_to_logger_agent, transfer_to_complete_response]
    
    # Create user-specific prompt
    coach_prompt = create_coach_prompt(user_id)
    
    coach_agent = create_react_agent(
        get_model(),
        prompt=coach_prompt,
        tools=all_tools,
        name="coach_agent",
    )
    
    return coach_agent


async def create_orchestration_agent(user_id: str):
    """Create the orchestration agent using vanilla react agent with Command-based quick_response."""
    # Import command-based quick response tool only
    from tools.quick_response_command_tool import create_quick_response_command_tool
    
    # Create tools that use Command to route to END
    quick_response_tool = create_quick_response_command_tool()
    
    # Combine handoff tools with command-based response tools
    all_tools = [transfer_to_logger_agent, transfer_to_coach_agent, quick_response_tool]
    
    # Use custom react agent with quick_response termination logic
    from agents.custom_react_agent import create_react_agent_with_quick_response_termination
    orchestration_agent = create_react_agent_with_quick_response_termination(
        get_model(),
        tools=all_tools,
        prompt=orchestration_prompt,
        name="orchestration_agent",
    )
    
    return orchestration_agent


# Note: Termination logic now built into custom react agent


async def create_agent_swarm(user_id: str) -> Tuple[Any, Any]:
    """Create the agent swarm for the given user and return (agent_app, mcp_client)."""
    # Create MCP client for this user
    mcp_client = create_mcp_client()
    
    try:
        # Create orchestration agent first (the main coordinator with built-in termination)
        orchestration_agent = await create_orchestration_agent(user_id)
        
        # Create specialized agents
        logger_agent = await create_logger_agent(mcp_client, user_id)
        coach_agent = await create_coach_agent(mcp_client, user_id)
        
        # Create complete response node as a pseudo-agent
        from agents.complete_response_node import create_complete_response_node
        complete_response_node = create_complete_response_node()
        
        # Create swarm with orchestration agent as default (routes to others)
        # Include the complete response node as part of the swarm
        agent_swarm = create_swarm(
            [orchestration_agent, logger_agent, coach_agent, complete_response_node], 
            default_active_agent="orchestration_agent"
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
        self.memory_initialized = False
    
    async def _ensure_memory_initialized(self):
        """Ensure memory service is initialized."""
        if not self.memory_initialized:
            try:
                config = get_configuration()
                if config.memory_enabled:
                    # Configure memory service
                    memory_config = MemoryConfiguration(
                        max_messages_per_user=config.memory_max_messages_per_user,
                        max_characters_per_message=config.memory_max_characters_per_message,
                        memory_cleanup_interval_hours=config.memory_cleanup_interval_hours,
                        max_conversation_age_days=config.memory_max_conversation_age_days,
                        enable_memory_compression=config.memory_enable_compression,
                        memory_storage_backend=config.memory_storage_backend
                    )
                    langchain_memory_service.config = memory_config
                    await langchain_memory_service.initialize()
                self.memory_initialized = True
            except Exception as e:
                print(f"Warning: Failed to initialize memory service: {e}")
                self.memory_initialized = True  # Don't keep retrying
    
    async def get_agent_for_user(self, user_id: str):
        """Get or create agent system for a specific user."""
        await self._ensure_memory_initialized()
        
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
    


    @traceable(
        name="pili_process_request",
        metadata={
            "component": "pili_agent_system",
            "operation": "full_request_processing"
        }
    )
    async def process_request(self, user_id: str, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Process a user request through the orchestration agent system."""
        try:
            # Create comprehensive tracing metadata
            initial_metadata = create_run_metadata(
                user_id=user_id,
                operation="process_request",
                session_id=session_id,
                message_length=len(message),
                user_cached=user_id in self.agent_cache,
                tracing_enabled=is_tracing_enabled()
            )
            
            # Add initial tracing metadata if tracing is enabled
            if is_tracing_enabled():
                from langsmith import get_current_run_tree
                run = get_current_run_tree()
                if run:
                    run.add_metadata(initial_metadata)
                    run.add_tags(["pili-fitness-chatbot", "agent-orchestration", f"user-{user_id}"])
            
            # Ensure memory is initialized
            await self._ensure_memory_initialized()
            
            # Get conversation context for LLM
            conversation_context = ""
            config = get_configuration()
            if config.memory_enabled:
                conversation_context = await langchain_memory_service.get_conversation_context(
                    user_id=user_id,
                    session_id=session_id
                )
            
            # Get agent system for user
            agent_app = await self.get_agent_for_user(user_id)
            
            # Format user message with datetime, user context, and conversation history
            formatted_message = format_user_message_with_context(user_id, message)
            if conversation_context:
                formatted_message = conversation_context + formatted_message
            
            # Prepare initial state with user context
            initial_state = {
                "messages": [{"role": "user", "content": formatted_message}],
                "user_id": user_id,  # Include user_id in state
                "session_id": session_id  # Include session_id in state
            }
            
            # Run the agent system with user-specific configuration
            agent_config = {
                "configurable": {
                    "thread_id": f"{user_id}_{session_id}_{uuid.uuid4()}", 
                    "user_id": user_id,
                    "session_id": session_id
                }
            }
            
            result = await agent_app.ainvoke(initial_state, config=agent_config)
            
                        # Extract and analyze the agent execution result
            messages = result.get("messages", [])
            if messages:
                final_message = messages[-1]
                
                # Handle different message types for response extraction
                response = None
                
                # Check if final message has quick_response tool call (terminated by custom react agent)
                if hasattr(final_message, 'tool_calls') and final_message.tool_calls:
                    for tool_call in final_message.tool_calls:
                        if tool_call.get('name') == 'quick_response':
                            # Simulate quick_response execution to get the response
                            args = tool_call.get('args', {})
                            query_type = args.get('query_type', 'casual')
                            user_query = args.get('user_query', '')
                            user_id = args.get('user_id', 'test_user')
                            
                            # Import and execute quick_response tool logic
                            from tools.quick_response_command_tool import create_quick_response_command_tool
                            quick_response_tool = create_quick_response_command_tool()
                            
                            # Execute the tool to get the response
                            try:
                                # Call the tool directly with proper parameters
                                tool_result = quick_response_tool.func(
                                    query_type=query_type,
                                    user_query=user_query,
                                    user_id=user_id,
                                    state={'messages': messages},
                                    tool_call_id='quick_response_sim'
                                )
                                response = tool_result.content
                            except Exception as e:
                                print(f"Quick response tool error: {e}")
                                response = f"Hello! 👋 Ready to help you achieve your fitness goals!"
                            break
                
                # If no quick_response tool call found, handle normally
                if response is None:
                    if hasattr(final_message, 'content'):
                        content = final_message.content
                        
                        # If it's a ToolMessage from quick_response, use content directly
                        if hasattr(final_message, 'name') and final_message.name == 'quick_response':
                            response = content
                        # Check for quick_response anywhere in the messages (should be final)
                        elif any(hasattr(msg, 'name') and msg.name == 'quick_response' for msg in messages[-5:]):
                            # Find the last quick_response message
                            for msg in reversed(messages):
                                if hasattr(msg, 'name') and msg.name == 'quick_response':
                                    response = msg.content
                                    break
                        # If it's structured content, try to parse it
                        elif isinstance(content, str) and content.startswith('{"name"'):
                            try:
                                import json
                                parsed = json.loads(content)
                                if "parameters" in parsed and "response" in parsed["parameters"]:
                                    response = parsed["parameters"]["response"]
                                else:
                                    response = content
                            except:
                                response = content
                        else:
                            response = content
                    else:
                        response = str(final_message)
                
                # Analyze what actually happened during execution
                agent_names = set()
                tool_calls = []
                ai_messages = []
                
                for msg in messages:
                    # Track agent names
                    if hasattr(msg, 'name') and msg.name:
                        agent_names.add(msg.name)
                    
                    # Track tool calls and responses
                    if isinstance(msg, langchain_core.messages.tool.ToolMessage):
                        tool_calls.append({
                            "tool_name": msg.name,
                            "tool_response": msg.content[:2000] + "..." if len(msg.content) > 2000 else msg.content
                        })
                    
                    # Track AI messages (assistant responses)
                    if isinstance(msg, langchain_core.messages.ai.AIMessage) and msg.content:
                        ai_messages.append({
                            "content": msg.content[:500] + "..." if len(msg.content) > 500 else msg.content,
                            "agent": getattr(msg, 'name', 'assistant')
                        })
                
                # Create comprehensive execution summary
                execution_summary = []
                
                if agent_names:
                    execution_summary.append(f"Agents: {', '.join(agent_names)}")
                
                if tool_calls:
                    tool_summary = []
                    for tool in tool_calls:
                        tool_summary.append(f"{tool['tool_name']} → {tool['tool_response']}")
                    execution_summary.append(f"Tools: {' | '.join(tool_summary)}")
                
                if ai_messages:
                    ai_summary = []
                    for ai_msg in ai_messages:
                        ai_summary.append(f"{ai_msg['agent']}: {ai_msg['content']}")
                    execution_summary.append(f"AI responses: {' | '.join(ai_summary)}")
                
                execution_summary.append(f"Total messages: {len(messages)}")
                
            else:
                response = "I'm sorry, I couldn't process your request right now."
                execution_summary = ["No agent response generated"]
            
            # Add execution results to trace
            if is_tracing_enabled():
                from langsmith import get_current_run_tree
                run = get_current_run_tree()
                if run:
                    execution_metadata = create_run_metadata(
                        user_id=user_id,
                        operation="agent_execution_complete",
                        message_count=len(messages),
                        execution_summary_length=len(execution_summary),
                        response_length=len(response),
                        agents_used=len(agent_names) if 'agent_names' in locals() else 0,
                        tools_called=len(tool_calls) if 'tool_calls' in locals() else 0,
                        ai_messages_count=len(ai_messages) if 'ai_messages' in locals() else 0
                    )
                    run.add_metadata(execution_metadata)
            
            # Prepare final result directly from orchestration agent
            final_result = {
                "response": response,
                "logs": [{
                    "agent_system": "langgraph_swarm_orchestration",
                    "user_id": user_id,
                    "message_count": len(messages),
                    "execution_summary": execution_summary
                }],
                "chain_of_thought": execution_summary.copy(),
                "execution_summary": execution_summary
            }
            
            # Add conversation exchange to memory
            app_config = get_configuration()
            if app_config.memory_enabled:
                await langchain_memory_service.add_exchange(
                    user_id=user_id,
                    session_id=session_id,
                    user_message=message,
                    ai_response=final_result["response"]
                )
            
            # Add final result metadata to trace
            if is_tracing_enabled():
                from langsmith import get_current_run_tree
                run = get_current_run_tree()
                if run:
                    final_metadata = create_run_metadata(
                        user_id=user_id,
                        operation="orchestration_complete",
                        final_response_length=len(final_result["response"]),
                        memory_enabled=app_config.memory_enabled,
                        using_orchestration_agent=True,
                        success=True
                    )
                    run.add_metadata(final_metadata)
            
            return final_result
            
        except Exception as e:
            print(f"Error in agent system for user {user_id}: {e}")
            
            # Add error to trace
            if is_tracing_enabled():
                from langsmith import get_current_run_tree
                run = get_current_run_tree()
                if run:
                    error_metadata = create_run_metadata(
                        user_id=user_id,
                        operation="process_request_error",
                        success=False,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    run.add_metadata(error_metadata)
            
            error_summary = [f"Error: {str(e)}"]
            return {
                "response": "I'm sorry, something went wrong. Please try again! 💪",
                "logs": [{"error": str(e), "agent_system": "failed", "user_id": user_id}],
                "chain_of_thought": error_summary,
                "execution_summary": error_summary
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
        
        # Also shutdown memory service
        try:
            await langchain_memory_service.shutdown()
        except Exception as e:
            print(f"Error shutting down memory service: {e}")
    
    async def get_user_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a specific user."""
        await self._ensure_memory_initialized()
        
        try:
            stats = await langchain_memory_service.get_user_memory_stats(user_id, "default")
            return stats
        except Exception as e:
            return {
                "user_id": user_id,
                "has_memory": False,
                "error": str(e)
            }
    
    async def clear_user_memory(self, user_id: str, session_id: Optional[str] = None):
        """Clear memory for a specific user."""
        await self._ensure_memory_initialized()
        
        try:
            await langchain_memory_service.clear_user_memory(user_id, session_id)
            return {"success": True, "message": f"Memory cleared for user {user_id}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global agent system instance
agent_system = PiliAgentSystem() 