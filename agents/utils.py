"""Utility functions for Pili fitness agents."""

import httpx
import json
import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from config.settings import settings


# HTTP client for MCP server communication
httpx_client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0),
    follow_redirects=True
)


async def get_mcp_tools() -> List[Dict[str, Any]]:
    """Fetch available tools from MCP server."""
    try:
        response = await httpx_client.post(
            settings.mcp_base_url,
            json={
                "method": "tools/list",
                "params": {}
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("result", {}).get("tools", [])
        else:
            print(f"Failed to get MCP tools: {response.status_code}")
            return []
            
    except httpx.TimeoutException:
        print("⏰ Request timed out getting MCP tools")
        return []
    except Exception as e:
        print(f"❌ Error getting MCP tools: {str(e)}")
        return []


async def get_mcp_resources() -> List[Dict[str, Any]]:
    """Fetch available resources from MCP server."""
    try:
        response = await httpx_client.post(
            settings.mcp_base_url,
            json={
                "method": "resources/list", 
                "params": {}
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("result", {}).get("resources", [])
        else:
            print(f"Failed to get MCP resources: {response.status_code}")
            return []
            
    except httpx.TimeoutException:
        print("⏰ Request timed out getting MCP resources")
        return []
    except Exception as e:
        print(f"❌ Error getting MCP resources: {str(e)}")
        return []


async def execute_mcp_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Execute a tool via MCP server and return the result."""
    try:
        mcp_request = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": tool_args
            }
        }
        
        response = await httpx_client.post(
            settings.mcp_base_url,
            json=mcp_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("result"):
                content = result.get("result", {}).get("content", "")
                return content if isinstance(content, str) else json.dumps(content)
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                return f"Tool execution failed: {error_msg}"
        else:
            return f"Failed to execute tool (Status: {response.status_code})"
            
    except httpx.TimeoutException:
        return "⏰ Tool execution timed out"
    except Exception as e:
        return f"❌ Error executing tool: {str(e)}"


def create_tool_spec_for_llm(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MCP tool to LangChain-compatible format for LLM use."""
    return {
        "type": "function",
        "function": {
            "name": tool.get("name", "unknown_tool"),
            "description": tool.get("description", "No description available"),
            "parameters": tool.get("inputSchema", {})
        }
    }


async def structured_agent_stream(
    agent_app, 
    initial_state: Dict[str, Any], 
    config: Dict[str, Any],
    chat_id: str = None,
    user_id: str = None,
    session_id: str = "default",
    user_message: str = None
) -> AsyncGenerator[str, None]:
    """
    Create a structured streaming response from agent execution.
    
    Processes real-time agent updates and formats them for easy client consumption.
    Returns structured JSON chunks that clients can easily parse and display.
    
    Args:
        agent_app: The compiled LangGraph agent application
        initial_state: Initial state for agent execution
        config: Agent configuration
        chat_id: Optional chat completion ID
        user_id: User ID for context
        session_id: Session ID for memory management
        user_message: Original user message for memory storage
        
    Yields:
        Formatted JSON strings for streaming response
    """
    if not chat_id:
        chat_id = f"chatcmpl-{int(time.time())}"
    
    created_time = int(time.time())
    
    # Initial metadata chunk
    initial_chunk = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created_time,
        "model": "pili-orchestration-swarm",
        "choices": [{
            "index": 0,
            "delta": {"role": "assistant", "content": ""},
            "finish_reason": None
        }],
        "metadata": {
            "user_id": user_id,
            "session_id": session_id,
            "stream_type": "agent_execution",
            "status": "started"
        }
    }
    yield f"data: {json.dumps(initial_chunk)}\n\n"
    
    # Track agent execution progress
    agent_updates = []
    tool_calls = []
    current_agent = None
    final_response = ""
    
    try:
        # Stream agent execution
        async for event in agent_app.astream(initial_state, config=config):
            event_type = "agent_update"
            
            # Process different types of updates
            for node, update in event.items():
                if update is None:
                    continue
                
                # Handle different update types
                if isinstance(update, dict):
                    # Check for messages
                    messages_key = next((k for k in update.keys() if "messages" in k), None)
                    
                    if messages_key and update[messages_key]:
                        messages = update[messages_key]
                        last_message = messages[-1]
                        
                        # Track agent changes
                        if hasattr(last_message, 'name') and last_message.name:
                            if current_agent != last_message.name:
                                current_agent = last_message.name
                                
                                # Send agent change notification
                                agent_chunk = {
                                    "id": chat_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_time,
                                    "model": "pili-orchestration-swarm",
                                    "choices": [{
                                        "index": 0,
                                        "delta": {},
                                        "finish_reason": None
                                    }],
                                    "metadata": {
                                        "stream_type": "agent_change",
                                        "current_agent": current_agent,
                                        "node": node,
                                        "status": "processing"
                                    }
                                }
                                yield f"data: {json.dumps(agent_chunk)}\n\n"
                        
                        # Handle AI messages (final responses)
                        if hasattr(last_message, 'content') and last_message.content:
                            content = last_message.content
                            if content != final_response:  # New content
                                final_response = content
                                
                                # Stream content progressively
                                words = content.split()
                                for i, word in enumerate(words):
                                    word_chunk = {
                                        "id": chat_id,
                                        "object": "chat.completion.chunk", 
                                        "created": created_time,
                                        "model": "pili-orchestration-swarm",
                                        "choices": [{
                                            "index": 0,
                                            "delta": {"content": f"{word} " if i < len(words) - 1 else word},
                                            "finish_reason": None
                                        }],
                                        "metadata": {
                                            "stream_type": "content",
                                            "agent": current_agent or "orchestration",
                                            "word_index": i,
                                            "total_words": len(words)
                                        }
                                    }
                                    yield f"data: {json.dumps(word_chunk, ensure_ascii=False)}\n\n"
                                    await asyncio.sleep(0.05)  # Smooth word-by-word streaming
                        
                        # Handle tool calls
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            for tool_call in last_message.tool_calls:
                                tool_info = {
                                    "name": getattr(tool_call, 'name', 'unknown'),
                                    "args": getattr(tool_call, 'args', {})
                                }
                                tool_calls.append(tool_info)
                                
                                # Send tool call notification
                                tool_chunk = {
                                    "id": chat_id,
                                    "object": "chat.completion.chunk",
                                    "created": created_time,
                                    "model": "pili-orchestration-swarm", 
                                    "choices": [{
                                        "index": 0,
                                        "delta": {},
                                        "finish_reason": None
                                    }],
                                    "metadata": {
                                        "stream_type": "tool_call",
                                        "tool_name": tool_info["name"],
                                        "agent": current_agent or "orchestration",
                                        "status": "executing"
                                    }
                                }
                                yield f"data: {json.dumps(tool_chunk)}\n\n"
                
                # Track updates for summary
                agent_updates.append({
                    "node": node,
                    "agent": current_agent,
                    "update_type": type(update).__name__
                })
        
        # Add conversation to memory if enabled and we have the necessary data
        if user_id and user_message and final_response:
            try:
                from config.settings import get_configuration
                from services.langchain_memory_service import langchain_memory_service
                
                app_config = get_configuration()
                if app_config.memory_enabled:
                    await langchain_memory_service.add_exchange(
                        user_id=user_id,
                        session_id=session_id,
                        user_message=user_message,
                        ai_response=final_response
                    )
            except Exception as e:
                print(f"Warning: Failed to add exchange to memory: {e}")
        
        # Final summary chunk
        summary_chunk = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": "pili-orchestration-swarm",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }],
            "metadata": {
                "stream_type": "execution_complete",
                "total_updates": len(agent_updates),
                "tools_used": len(tool_calls),
                "final_agent": current_agent,
                "final_response_length": len(final_response),
                "status": "completed"
            }
        }
        yield f"data: {json.dumps(summary_chunk)}\n\n"
        
    except Exception as e:
        # Error handling chunk
        error_chunk = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": "pili-orchestration-swarm",
            "choices": [{
                "index": 0,
                "delta": {"content": "I'm sorry, something went wrong. Please try again! 💪"},
                "finish_reason": "stop"
            }],
            "metadata": {
                "stream_type": "error",
                "error": str(e),
                "status": "failed"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
    
    # Final DONE signal
    yield "data: [DONE]\n\n"


def extract_user_id_from_args(tool_args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Ensure user_id is present in tool arguments."""
    if 'user_id' not in tool_args:
        tool_args['user_id'] = user_id
    return tool_args


def print_stream(stream):
    """Print LangGraph stream updates for debugging."""
    for namespace, update in stream:
        for node, node_updates in update.items():
            if node_updates is None:
                continue

            if isinstance(node_updates, (dict, tuple)):
                node_updates_list = [node_updates]
            elif isinstance(node_updates, list):
                node_updates_list = node_updates
            else:
                raise ValueError(f"Unexpected update type: {type(node_updates)}")

            for node_update in node_updates_list:
                if isinstance(node_update, tuple):
                    continue
                    
                # Look for messages in the update
                messages_key = next(
                    (k for k in node_update.keys() if "messages" in k.lower()), None
                )
                if messages_key is not None:
                    messages = node_update[messages_key]
                    if messages and hasattr(messages[-1], 'pretty_print'):
                        messages[-1].pretty_print()


async def close_httpx_client():
    """Close the HTTP client connection."""
    await httpx_client.aclose() 

def print_stream(stream):
    """
    Print agent stream updates in a structured format.
    Similar to the provided sample but enhanced for agent system.
    """
    for ns, update in stream:
        for node, node_updates in update.items():
            if node_updates is None:
                continue

            if isinstance(node_updates, (dict, tuple)):
                node_updates_list = [node_updates]
            elif isinstance(node_updates, list):
                node_updates_list = node_updates
            else:
                raise ValueError(f"Unexpected update type: {type(node_updates)}")

            for node_update in node_updates_list:
                if isinstance(node_update, tuple):
                    continue
                    
                # Look for messages in the update
                messages_key = next(
                    (k for k in node_update.keys() if "messages" in k), None
                )
                
                if messages_key is not None and node_update[messages_key]:
                    last_message = node_update[messages_key][-1]
                    
                    # Pretty print the message
                    if hasattr(last_message, 'pretty_print'):
                        last_message.pretty_print()
                    else:
                        print(f"[{node}] {last_message}")
                else:
                    print(f"[{node}] Update: {node_update}")