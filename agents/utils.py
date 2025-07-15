"""Utility functions for Pili fitness agents."""

import httpx
import json
from typing import Dict, Any, List, Optional
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
    """Convert MCP tool definition to LLM-compatible tool specification."""
    if not isinstance(tool, dict) or not tool.get("name"):
        return None
        
    return {
        "type": "function",
        "function": {
            "name": tool.get("name", ""),
            "description": tool.get("description", ""),
            "parameters": tool.get("inputSchema", {"type": "object", "properties": {}})
        }
    }


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