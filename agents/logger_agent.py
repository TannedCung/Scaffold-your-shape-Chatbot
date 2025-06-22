from typing import Dict, Any, Optional, List
import httpx
import json
import re
from datetime import datetime
from services.llm_service import llm_service
from config.settings import settings


class LoggerAgent:
    """Agent responsible for interacting with Scaffold Your Shape application via MCP server."""
    
    def __init__(self):
        self.mcp_base_url = settings.mcp_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.conversation_history = []
    
    async def handle_request(self, user_id: str, message: str) -> str:
        """Handle requests by fetching available tools and letting LLM decide which to use."""
        try:
            # Get available tools from MCP server
            available_tools = await self._get_available_tools()
            
            if not available_tools:
                return "❌ Unable to connect to Scaffold Your Shape service. Please check if the service is running."
            
            # Process user query with available tools
            return await self._process_user_query(user_id, message, available_tools)
            
        except Exception as e:
            return f"❌ Error processing request: {str(e)}"
    
    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from MCP server."""
        try:
            # Request available tools from MCP server
            response = await self.client.post(
                f"{self.mcp_base_url}",
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
                print(f"Failed to get tools: {response.status_code}")
                return []
                
        except httpx.TimeoutException:
            print("⏰ Request timed out getting tools")
            return []
        except Exception as e:
            print(f"❌ Error getting tools: {str(e)}")
            return []
    
    async def _get_available_resources(self) -> List[Dict[str, Any]]:
        """Fetch available resources from MCP server."""
        try:
            # Request available resources from MCP server
            response = await self.client.post(
                f"{self.mcp_base_url}",
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
                print(f"Failed to get resources: {response.status_code}")
                return []
                
        except httpx.TimeoutException:
            print("⏰ Request timed out getting resources")
            return []
        except Exception as e:
            print(f"❌ Error getting resources: {str(e)}")
            return []
    
    async def _process_user_query(self, user_id: str, user_query: str, available_tools: List[Dict[str, Any]]) -> str:
        """Process the user query and return the response using LLM tool selection."""
        
        # Initialize conversation with system message
        if not self.conversation_history:
            self.conversation_history = [
                {
                    "role": "system",
                    "content": """You are Pili, an enthusiastic fitness assistant that helps users interact with the Scaffold Your Shape fitness tracking system. 

You have access to various tools for logging activities, managing clubs, and retrieving fitness data. 

When a user asks for something:
1. Analyze their request carefully
2. Use the appropriate tools available to fulfill their request
3. Be encouraging and use fitness emojis in your responses
4. Provide helpful feedback about what you've accomplished

Available tools will be provided to you dynamically from the MCP server."""
                }
            ]
        
        # Add user message to conversation
        self.conversation_history.append({
            "role": "user", 
            "content": user_query
        })
        
        # Create tool specifications for LLM
        tools_for_llm = []
        
        for tool in available_tools:
            if isinstance(tool, dict) and tool.get("name"):
                tool_spec = {
                    "type": "function",
                    "function": {
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {"type": "object", "properties": {}})
                    }
                }
                tools_for_llm.append(tool_spec)
        
        # Get LLM response with tool calling capability
        if tools_for_llm:
            llm_response = await llm_service.generate_response_with_tools(
                "logger_agent",
                user_query,
                f"""You are Pili, a fitness assistant. The user said: "{user_query}"
                
                User ID: {user_id}
                
                Use the available tools to help the user with their fitness tracking needs. 
                Be encouraging and provide helpful feedback about what you're doing.""",
                conversation_history=self.conversation_history,
                tools=tools_for_llm
            )
        else:
            # No tools available, generate a response without tools
            llm_response = await llm_service.generate_response(
                "logger_agent",
                user_query,
                f"""You are Pili, a fitness assistant. The user said: "{user_query}"
                
                User ID: {user_id}
                
                Unfortunately, the fitness tracking tools are currently unavailable. 
                Acknowledge the user's fitness activity and provide encouragement, 
                but explain that you can't log their data right now.""",
                conversation_history=self.conversation_history
            )
        
        # Parse LLM response and handle tool calls
        if hasattr(llm_response, 'tool_calls') and llm_response.tool_calls:
            # Handle tool calls
            tool_results = []
            
            for tool_call in llm_response.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Add user_id to tool arguments if not present
                if 'user_id' not in tool_args:
                    tool_args['user_id'] = user_id
                
                # Execute the tool
                tool_result = await self._execute_tool(tool_name, tool_args)
                tool_results.append(tool_result)
                
                # Add tool result to conversation
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # Get final response from LLM incorporating tool results
            final_response = await llm_service.generate_response(
                "logger_agent_final",
                user_query,
                f"""Based on the tool execution results, provide a friendly, encouraging response to the user.
                
                User request: "{user_query}"
                Tool results: {json.dumps(tool_results, indent=2)}
                
                Be enthusiastic, use fitness emojis, and explain what was accomplished.""",
                conversation_history=self.conversation_history
            )
            
            # Add final response to conversation
            self.conversation_history.append({
                "role": "assistant",
                "content": final_response
            })
            
            return final_response
        
        else:
            # No tool calls needed, just return LLM response
            response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response_content
            })
            
            return response_content
    
    async def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Execute a tool via MCP server."""
        try:
            # Prepare MCP request
            mcp_request = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": tool_args
                }
            }
            
            # Send request to MCP server
            response = await self.client.post(
                f"{self.mcp_base_url}",
                json=mcp_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return result.get("result", {}).get("content", "Tool executed successfully")
                else:
                    return f"Tool execution failed: {result.get('error', 'Unknown error')}"
            else:
                return f"Failed to execute tool (Status: {response.status_code})"
                
        except httpx.TimeoutException:
            return "⏰ Tool execution timed out"
        except Exception as e:
            return f"❌ Error executing tool: {str(e)}"
    
    def clear_conversation_history(self):
        """Clear conversation history for a fresh start."""
        self.conversation_history = []


# Create global instance
logger_agent = LoggerAgent() 