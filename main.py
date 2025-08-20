from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from models.chat import ChatRequest, ChatResponse, MemoryStatsRequest, ClearMemoryRequest
from models.memory import MemorySearchQuery
from agents.agent import agent_system
from services.langchain_memory_service import langchain_memory_service
from config.settings import get_configuration
import json
import time
import asyncio
import uuid

app = FastAPI(
    title="Pili Exercise Chatbot API",
    description="A multiagent chatbot named Pili for tracking exercises using LangGraph and FastAPI.",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs"
)

api_router = APIRouter(prefix="/api")



@api_router.post("/chat", tags=["Chatbot"])
async def chat_endpoint(request: ChatRequest):
    """
    Chat with Pili, the Exercise Tracker Bot.
    
    Uses LangGraph agent swarm with specialized agents:
    - Logger Agent: Handles activity logging, club management, data retrieval
    - Coach Agent: Provides coaching advice, workout planning, progress analysis
    
    Supports both regular and streaming responses (set stream=true for streaming).
    
    Pili can help you with:
    - **Log exercises**: "I did 20 pushups"
    - **Track progress**: "Show my progress" 
    - **Join clubs**: "Join club fitness"
    - **Exit clubs**: "Leave club fitness"
    - **Coaching advice**: "Create a workout plan"
    - **Get help**: "help"
    
    **Parameters:**
    - **user_id**: Unique user identifier
    - **message**: User's message to Pili
    - **stream**: Optional boolean to enable streaming response (default: false)
    """
    try:
        if request.stream:
            # For streaming, use the structured agent stream
            from agents.utils import structured_agent_stream
            
            # Get agent system for user
            agent_app = await agent_system.get_agent_for_user(request.user_id)
            
            # Get conversation context for LLM
            conversation_context = ""
            config = get_configuration()
            if config.memory_enabled:
                conversation_context = await langchain_memory_service.get_conversation_context(
                    user_id=request.user_id,
                    session_id=request.session_id or "default"
                )
            
            # Format user message with context
            from agents.agent import format_user_message_with_context
            formatted_message = format_user_message_with_context(request.user_id, request.message)
            if conversation_context:
                formatted_message = conversation_context + formatted_message
            
            # Prepare initial state
            initial_state = {
                "messages": [{"role": "user", "content": formatted_message}],
                "user_id": request.user_id,
                "session_id": request.session_id or "default"
            }
            
            # Agent configuration
            agent_config = {
                "configurable": {
                    "thread_id": f"{request.user_id}_{request.session_id or 'default'}_{uuid.uuid4()}", 
                    "user_id": request.user_id,
                    "session_id": request.session_id or "default"
                }
            }
            
            # Create structured streaming response
            return StreamingResponse(
                structured_agent_stream(
                    agent_app=agent_app,
                    initial_state=initial_state,
                    config=agent_config,
                    user_id=request.user_id,
                    session_id=request.session_id or "default",
                    user_message=request.message
                ),
                media_type="text/plain"
            )
        else:
            # Non-streaming response using orchestration agent system
            agent_result = await agent_system.process_request(
                request.user_id,
                request.message,
                request.session_id or "default"
            )
            
            return ChatResponse(
                response=agent_result["response"],
                logs=agent_result["logs"]
            )
        
    except Exception as e:
        # Log the error with traceback
        import traceback
        traceback.print_exc()
        print(f"Chat processing error: {e}")
        
        if request.stream:
            # Return streaming error
            async def error_stream():
                error_chunk = {
                    "id": f"chatcmpl-error-{int(time.time())}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "pili-orchestration-swarm",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": "I'm sorry, something went wrong. Please try again! 💪"},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(error_stream(), media_type="text/plain")
        else:
            return ChatResponse(
                response="I'm sorry, something went wrong. Please try again! 💪",
                logs=[{"error": str(e), "agent_system": "failed"}]
            )


@api_router.get("/memory/stats/{user_id}", tags=["Memory"])
async def get_memory_stats(user_id: str):
    """
    Get memory statistics for a specific user.
    
    Returns information about the user's conversation history including:
    - Number of messages stored
    - Session information
    - Memory timestamps
    """
    try:
        stats = await agent_system.get_user_memory_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/memory/global-stats", tags=["Memory"])
async def get_global_memory_stats():
    """
    Get global memory statistics across all users.
    
    Returns system-wide memory usage information.
    """
    try:
        config = get_configuration()
        if not config.memory_enabled:
            return {"memory_enabled": False, "message": "Memory is disabled"}
            
        stats = await langchain_memory_service.get_global_memory_stats()
        return {
            "memory_enabled": True,
            "stats": stats.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/memory/clear", tags=["Memory"])
async def clear_user_memory(request: ClearMemoryRequest):
    """
    Clear conversation memory for a specific user.
    
    Optionally specify a session_id to clear only a specific session,
    otherwise clears all sessions for the user.
    """
    try:
        result = await agent_system.clear_user_memory(request.user_id, request.session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/memory/search", tags=["Memory"])
async def search_memory(query: MemorySearchQuery):
    """
    Search through conversation history for a specific user.
    
    Allows searching through past conversations using text-based queries.
    """
    try:
        config = get_configuration()
        if not config.memory_enabled:
            raise HTTPException(status_code=503, detail="Memory service is disabled")
            
        results = await langchain_memory_service.search_conversations(
            user_id=query.user_id,
            query=query.query,
            max_results=query.max_results
        )
        return {
            "query": query.query,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/memory/conversation/{user_id}", tags=["Memory"])
async def get_conversation_history(
    user_id: str, 
    session_id: str = "default", 
    limit: int = 50
):
    """
    Get conversation history for a specific user and session.
    
    Returns the conversation messages in chronological order.
    """
    try:
        config = get_configuration()
        if not config.memory_enabled:
            raise HTTPException(status_code=503, detail="Memory service is disabled")
            
        conversation_data = await langchain_memory_service.get_conversation_history_formatted(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        return conversation_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "pili-exercise-chatbot"}


@api_router.get("/docs", include_in_schema=False)
async def custom_docs_redirect():
    """Redirect to the FastAPI Swagger UI documentation."""
    return RedirectResponse(url="/api/docs")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to the API docs."""
    return RedirectResponse(url="/api/docs")


@app.get("/api/health")
async def health_check_detailed():
    """Health check endpoint with system status."""
    try:
        config = get_configuration()
        
        # Test MCP connection
        from services.mcp_client import create_mcp_client
        mcp_client = create_mcp_client()
        try:
            mcp_status = await mcp_client.test_connection()
        finally:
            await mcp_client.close()
        
    except Exception as e:
        mcp_status = {"status": "error", "error": str(e)}
    
    return {
        "status": "healthy", 
        "service": "pili-exercise-chatbot",
        "agent_system": "langgraph_swarm",
        "llm_provider": config.llm_provider,
        "llm_model": config.openai_model if config.llm_provider == "openai" else config.local_llm_model,
        "mcp_status": mcp_status
    }


@app.post("/api/debug-agent")
async def debug_agent(request: ChatRequest):
    """Debug endpoint to test agent system directly."""
    try:
        # Test orchestration agent system processing
        result = await agent_system.process_request(request.user_id, request.message)
        
        return {
            "agent_response": result["response"],
            "logs": result["logs"],
            "chain_of_thought": result.get("chain_of_thought", []),
            "execution_summary": result.get("execution_summary", []),
            "orchestrated": True,
            "note": "Direct orchestration agent system testing"
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/test-config")
async def test_config():
    """Test endpoint to verify configuration."""
    try:
        config = get_configuration()
        
        return {
            "llm_provider": config.llm_provider,
            "model": config.openai_model if config.llm_provider == "openai" else config.local_llm_model,
            "base_url": config.local_llm_base_url if config.llm_provider != "openai" else "https://api.openai.com",
            "mcp_base_url": config.mcp_base_url,
            "note": "Configuration test endpoint"
        }
        
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/debug-mcp")
async def debug_mcp():
    """Debug endpoint to test MCP client and tool schemas."""
    try:
        from services.mcp_client import create_mcp_client
        
        mcp_client = create_mcp_client()
        try:
            # Test connection
            connection_test = await mcp_client.test_connection()
            
            # Get raw tools
            raw_tools = await mcp_client.list_tools()
            
            # Get LangChain tools for a test user
            test_user_id = "debug-user"
            langchain_tools = await mcp_client.get_tools(test_user_id)
            
            # Detailed info
            tool_details = []
            for tool in raw_tools[:3]:  # First 3 tools
                tool_info = {
                    "name": tool.get("name", "unnamed"),
                    "description": tool.get("description", "No description"),
                    "input_schema": tool.get("inputSchema", {}),
                    "has_schema": bool(tool.get("inputSchema"))
                }
                tool_details.append(tool_info)
            
            langchain_tool_details = []
            for tool in langchain_tools[:3]:  # First 3 tools
                tool_detail = {
                    "name": tool.name,
                    "description": tool.description[:100] + "..." if len(tool.description) > 100 else tool.description,
                    "has_args_schema": hasattr(tool, 'args_schema') and tool.args_schema is not None,
                    "tool_type": str(type(tool).__name__)
                }
                
                # Add schema fields if available
                if hasattr(tool, 'args_schema') and tool.args_schema:
                    if hasattr(tool.args_schema, 'model_fields'):
                        tool_detail["schema_fields"] = list(tool.args_schema.model_fields.keys())
                    elif hasattr(tool.args_schema, '__fields__'):
                        tool_detail["schema_fields"] = list(tool.args_schema.__fields__.keys())
                
                langchain_tool_details.append(tool_detail)
            
            return {
                "status": "success",
                "connection_test": connection_test,
                "raw_tools_count": len(raw_tools),
                "langchain_tools_count": len(langchain_tools),
                "sample_raw_tools": tool_details,
                "sample_langchain_tools": langchain_tool_details
            }
            
        finally:
            await mcp_client.close()
            
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/api/agent/clear-cache")
async def clear_agent_cache(user_id: str = None):
    """Clear agent cache for a specific user or all users."""
    try:
        if user_id:
            agent_system.clear_user_cache(user_id)
            return {"status": "success", "message": f"Cleared cache for user {user_id}"}
        else:
            agent_system.clear_all_cache()
            return {"status": "success", "message": "Cleared all agent caches"}
    except Exception as e:
        return {"error": str(e)}


app.include_router(api_router) 