"""MCP Server for Orchestrator Agent Quick Response Tool.

This module provides an MCP server that exposes the quick response tool
for the orchestrator agent to handle immediate responses to casual queries.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .quick_response_mcp_tool import create_quick_response_tool


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """Base MCP request model."""
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    """Base MCP response model."""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class OrchestratorMCPServer:
    """MCP Server for orchestrator agent tools."""
    
    def __init__(self):
        self.quick_response_tool = create_quick_response_tool()
        self.tools_registry = {
            "quick_response": self.quick_response_tool
        }
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        tools = []
        
        for tool_name, tool in self.tools_registry.items():
            tool_schema = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # Get schema from tool if available
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema.model_json_schema()
                tool_schema["inputSchema"] = {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", [])
                }
            
            tools.append(tool_schema)
        
        return {"tools": tools}
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with arguments."""
        if tool_name not in self.tools_registry:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools_registry[tool_name]
        
        try:
            # Call the tool
            if hasattr(tool, '_arun'):
                result = await tool._arun(**arguments)
            else:
                result = tool._run(**arguments)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ],
                "isError": False
            }
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Error: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP requests."""
        try:
            if request.method == "tools/list":
                result = await self.list_tools()
                return MCPResponse(result=result)
            
            elif request.method == "tools/call":
                tool_name = request.params.get("name")
                arguments = request.params.get("arguments", {})
                
                if not tool_name:
                    raise ValueError("Tool name is required for tools/call")
                
                result = await self.call_tool(tool_name, arguments)
                return MCPResponse(result=result)
            
            else:
                raise ValueError(f"Unsupported method: {request.method}")
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return MCPResponse(error={
                "code": -1,
                "message": str(e)
            })


# Global server instance
orchestrator_mcp_server = OrchestratorMCPServer()


# FastAPI app for the MCP server
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Orchestrator MCP Server")
    yield
    logger.info("Shutting down Orchestrator MCP Server")


app = FastAPI(
    title="Pili Orchestrator MCP Server",
    description="MCP server providing quick response tools for Pili's orchestrator agent",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/mcp", response_model=MCPResponse)
async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """Handle MCP requests."""
    return await orchestrator_mcp_server.handle_request(request)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "orchestrator_mcp_server"}


@app.get("/tools")
async def list_available_tools():
    """List available tools (for debugging)."""
    result = await orchestrator_mcp_server.list_tools()
    return result


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "tools.orchestrator_mcp_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

