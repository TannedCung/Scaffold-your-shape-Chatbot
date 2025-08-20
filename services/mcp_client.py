"""MCP Client for Pili fitness chatbot.

This module provides the PiliMCPClient class for managing connections to the
Scaffold Your Shape MCP server and loading LangChain tools and resources.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
import httpx
import json

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field, create_model
from config.settings import get_configuration


class PiliMCPClient:
    """Client for connecting to Scaffold Your Shape MCP server.
    
    Loads LangChain-compatible tools from the MCP server for use in agent workflows.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the Pili MCP client.
        
        Args:
            base_url: Base URL for the MCP server. If None, uses configuration.
        """
        self.config = get_configuration()
        self.base_url = base_url or self.config.mcp_base_url
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from MCP server."""
        try:
            response = await self.client.post(
                self.base_url,
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
                
        except Exception as e:
            print(f"Error getting MCP tools: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the MCP server."""
        try:
            response = await self.client.post(
                self.base_url,
                json={
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                },
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
                
        except Exception as e:
            return f"Error executing tool: {str(e)}"
    
    def _create_pydantic_model(self, tool_name: str, tool_schema: Dict[str, Any]) -> type[BaseModel]:
        """Create a Pydantic model from tool schema."""
        if not tool_schema or "properties" not in tool_schema:
            # Return generic model if no schema
            class GenericModel(BaseModel):
                pass
            return GenericModel
        
        properties = tool_schema["properties"]
        required_fields = tool_schema.get("required", [])
        pydantic_fields = {}
        
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            param_desc = param_info.get("description", "")
            is_required = param_name in required_fields
            
            # Map JSON schema types to Python types
            python_type = str  # Default
            if param_type == "integer":
                python_type = int
            elif param_type == "number":
                python_type = float
            elif param_type == "boolean":
                python_type = bool
            elif param_type == "array":
                python_type = list
            elif param_type == "object":
                python_type = dict
            
            # Create field
            if is_required:
                pydantic_fields[param_name] = (python_type, Field(description=param_desc))
            else:
                pydantic_fields[param_name] = (python_type, Field(default=None, description=param_desc))
        
        # Create dynamic model
        return create_model(f"{tool_name}Input", **pydantic_fields)
    
    def _create_tool_function(self, tool_name: str, tool_description: str, 
                            tool_schema: Dict[str, Any], user_id: str) -> BaseTool:
        """Create a LangChain tool from MCP tool definition."""
        
        # Create Pydantic model for validation
        InputModel = self._create_pydantic_model(tool_name, tool_schema)
        
        # Create the tool function
        @tool(tool_name, args_schema=InputModel, return_direct=False)
        async def mcp_tool_func(**kwargs) -> str:
            """Execute MCP tool with given arguments."""
            # Ensure user_id is present
            if "user_id" not in kwargs:
                kwargs["user_id"] = user_id
            
            # Remove None values for cleaner tool calls
            cleaned_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            return await self.call_tool(tool_name, cleaned_kwargs)
        
        # Enhance description with parameter info
        enhanced_description = tool_description
        if tool_schema and "properties" in tool_schema:
            properties = tool_schema["properties"]
            required = tool_schema.get("required", [])
            
            param_docs = []
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "string")
                param_desc = param_info.get("description", "")
                is_required = param_name in required
                required_marker = " (required)" if is_required else " (optional)"
                
                param_docs.append(f"- {param_name} ({param_type}){required_marker}: {param_desc}")
            
            if param_docs:
                enhanced_description = f"{tool_description}\n\nParameters:\n" + "\n".join(param_docs)
        
        # Update tool description
        mcp_tool_func.description = enhanced_description
        
        return mcp_tool_func
    
    async def get_tools(self, user_id: str) -> List[BaseTool]:
        """Get all tools as LangChain BaseTool objects for a specific user.
        
        Args:
            user_id: User ID to inject into tool calls
            
        Returns:
            List of LangChain tools ready for use with agents
        """
        raw_tools = await self.list_tools()
        langchain_tools = []
        
        for tool_data in raw_tools:
            if not isinstance(tool_data, dict) or not tool_data.get("name"):
                continue
                
            tool_name = tool_data.get("name", "")
            tool_description = tool_data.get("description", "")
            tool_schema = tool_data.get("inputSchema", {})
            
            try:
                langchain_tool = self._create_tool_function(
                    tool_name, tool_description, tool_schema, user_id
                )
                langchain_tools.append(langchain_tool)
            except Exception as e:
                print(f"Failed to create tool {tool_name}: {e}")
                continue
        
        return langchain_tools
    
    async def get_tool(self, tool_name: str, user_id: str) -> Optional[BaseTool]:
        """Get a specific tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            user_id: User ID to inject into tool calls
            
        Returns:
            LangChain tool or None if not found
        """
        raw_tools = await self.list_tools()
        
        for tool_data in raw_tools:
            if tool_data.get("name") == tool_name:
                tool_description = tool_data.get("description", "")
                tool_schema = tool_data.get("inputSchema", {})
                
                try:
                    return self._create_tool_function(
                        tool_name, tool_description, tool_schema, user_id
                    )
                except Exception as e:
                    print(f"Failed to create tool {tool_name}: {e}")
                    return None
        
        return None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to MCP server."""
        try:
            tools = await self.list_tools()
            return {
                "status": "connected",
                "tools_count": len(tools),
                "server_url": self.base_url
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "server_url": self.base_url
            }


# Factory function for creating client instances
def create_mcp_client(base_url: Optional[str] = None) -> PiliMCPClient:
    """Create a new MCP client instance.
    
    Args:
        base_url: Optional base URL override
        
    Returns:
        PiliMCPClient instance
    """
    return PiliMCPClient(base_url)


# Global client instance (for backwards compatibility)
mcp_client = create_mcp_client() 