from typing import Dict, Any, Optional, List
import httpx
import json
from datetime import datetime, timedelta
from services.llm_service import llm_service
from config.settings import settings


class CoachAgent:
    """Agent responsible for providing coaching advice and workout planning using dynamic MCP tools."""
    
    def __init__(self):
        self.mcp_base_url = settings.mcp_base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.conversation_history = []
    
    async def handle_request(self, user_id: str, message: str, logger_data: Optional[str] = None) -> str:
        """Handle coaching requests by fetching available tools and letting LLM decide which to use."""
        try:
            # Get available tools from MCP server
            available_tools = await self._get_available_tools()
            
            # Process user query with available tools and context from logger
            return await self._process_coaching_query(user_id, message, available_tools, logger_data)
            
        except Exception as e:
            return f"💪 I'm here to help with coaching advice! While I work on accessing fitness data, here's some general motivation: {str(e)[:50]}... Keep pushing forward! 🏃‍♀️"
    
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
                print(f"Failed to get coaching tools: {response.status_code}")
                return []
                
        except httpx.TimeoutException:
            print("⏰ Request timed out getting coaching tools")
            return []
        except Exception as e:
            print(f"❌ Error getting coaching tools: {str(e)}")
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
                print(f"Failed to get coaching resources: {response.status_code}")
                return []
                
        except httpx.TimeoutException:
            print("⏰ Request timed out getting coaching resources")
            return []
        except Exception as e:
            print(f"❌ Error getting coaching resources: {str(e)}")
            return []
    
    async def _process_coaching_query(self, user_id: str, user_query: str, available_tools: List[Dict[str, Any]], logger_data: Optional[str] = None) -> str:
        """Process the coaching query using LLM tool selection."""
        
        # Initialize conversation with system message
        if not self.conversation_history:
            self.conversation_history = [
                {
                    "role": "system",
                    "content": """You are Pili, an expert fitness coach providing personalized coaching advice and workout planning.

Your coaching specialties:
- Creating personalized workout plans
- Analyzing fitness progress and performance
- Providing motivation and encouragement
- Suggesting improvements based on data
- Setting realistic fitness goals
- Offering exercise technique advice

You have access to fitness tracking tools and data to provide data-driven coaching advice.

When coaching:
1. Be encouraging and motivational
2. Use fitness data to provide specific, personalized advice
3. Create realistic and achievable plans
4. Celebrate achievements and progress
5. Use fitness emojis appropriately
6. Provide actionable next steps

Available tools will be provided dynamically from the MCP server."""
                }
            ]
        
        # Add user message to conversation
        self.conversation_history.append({
            "role": "user", 
            "content": user_query
        })
        
        # Create tool specifications for LLM
        tools_for_llm = []
        print(f"Processing coaching tools for LLM: {available_tools}")
        
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
        
        
        # Include logger data context if available
        context_info = ""
        if logger_data:
            context_info = f"\n\nRecent activity context from Logger Agent: {logger_data}"
        
        # Get LLM response with tool calling capability
        if tools_for_llm:
            llm_response = llm_service.generate_response_with_tools(
                "coach_agent",
                user_query,
                f"""You are Pili, an expert fitness coach. The user said: "{user_query}"
                
                User ID: {user_id}
                {context_info}
                
                Provide personalized coaching advice using available tools to gather fitness data when needed.
                Be encouraging, motivational, and use specific data to make your coaching advice actionable.""",
                conversation_history=self.conversation_history,
                tools=tools_for_llm
            )
        else:
            # No tools available, provide general coaching advice
            llm_response = llm_service.generate_response(
                "coach_agent",
                user_query,
                f"""You are Pili, an expert fitness coach. The user said: "{user_query}"
                
                User ID: {user_id}
                {context_info}
                
                The fitness tracking tools are currently unavailable, but provide encouraging coaching advice based on the user's query.
                Be motivational, supportive, and offer general fitness guidance.""",
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
            
            # Get final coaching response from LLM incorporating tool results
            final_response = llm_service.generate_response(
                "coach_agent_final",
                user_query,
                f"""Based on the fitness data and tool results, provide expert coaching advice to the user.
                
                User request: "{user_query}"
                Tool results: {json.dumps(tool_results, indent=2)}
                Logger context: {logger_data if logger_data else "None"}
                
                Provide personalized coaching that:
                1. Uses the actual data to make specific recommendations
                2. Is encouraging and motivational
                3. Includes actionable next steps
                4. Celebrates any achievements found in the data
                5. Sets realistic goals based on current fitness level
                
                Be enthusiastic and use fitness emojis appropriately.""",
                conversation_history=self.conversation_history
            )
            
            # Add final response to conversation
            self.conversation_history.append({
                "role": "assistant",
                "content": final_response
            })
            
            return final_response
        
        else:
            # No tool calls needed, provide general coaching advice
            response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
            
            # Enhance with motivational coaching context
            enhanced_response = llm_service.generate_response(
                "coach_general",
                user_query,
                f"""You are Pili, an expert fitness coach. Provide encouraging coaching advice for: "{user_query}"
                
                Logger context: {logger_data if logger_data else "No recent activity data"}
                
                Provide motivational coaching advice that:
                1. Addresses their specific request
                2. Is encouraging and supportive
                3. Includes practical tips they can implement
                4. Uses fitness emojis appropriately
                5. Offers actionable next steps
                
                Base response context: {response_content}""",
                conversation_history=self.conversation_history
            )
            
            self.conversation_history.append({
                "role": "assistant",
                "content": enhanced_response
            })
            
            return enhanced_response
    
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
                return f"Failed to execute coaching tool (Status: {response.status_code})"
                
        except httpx.TimeoutException:
            return "⏰ Coaching tool execution timed out"
        except Exception as e:
            return f"❌ Error executing coaching tool: {str(e)}"
    
    def clear_conversation_history(self):
        """Clear conversation history for a fresh start."""
        self.conversation_history = []


# Create global instance
coach_agent = CoachAgent() 