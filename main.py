from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse, StreamingResponse
from models.chat import ChatRequest, ChatResponse
from agents.agent import agent_system
from config.settings import get_configuration
import json
import time
import asyncio

# LLM finalization imports
from openai import OpenAI

app = FastAPI(
    title="Pili Exercise Chatbot API",
    description="A multiagent chatbot named Pili for tracking exercises using LangGraph and FastAPI.",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs"
)

api_router = APIRouter(prefix="/api")


async def finalize_response(agent_result: dict, user_message: str) -> dict:
    """
    Use LLM to generate a friendly, summarized response based on agent result.
    
    Args:
        agent_result: The raw result from agent system containing response, logs, chain_of_thought
        user_message: The original user message for context
        
    Returns:
        dict: Enhanced result with finalized response
    """
    try:
        # Get configuration for LLM
        config = get_configuration()
        
        # Initialize LLM client based on configuration
        if config.llm_provider == "openai":
            client = OpenAI(api_key=config.openai_api_key)
            model_name = config.openai_model
        else:
            client = OpenAI(
                base_url=config.local_llm_base_url,
                api_key=config.local_llm_api_key or "dummy-key"
            )
            model_name = config.local_llm_model
        
        # Extract information from agent result
        original_response = agent_result.get("response", "")
        logs = agent_result.get("logs", [])
        chain_of_thought = agent_result.get("chain_of_thought", [])
        
        # Create finalization prompt
        finalization_prompt = f"""
You are Pili, a friendly fitness chatbot. Your job is to create a warm, personalized response based on the agent's work.

## User's original message:
{user_message}

## What the agent system did:
{original_response}

## Summary of actions taken:
{json.dumps(chain_of_thought, indent=2)}

## Your task:
1. Create a friendly, conversational response that acknowledges what was accomplished
2. Include a brief summary of what you did to help the user
3. Maintain Pili's encouraging, fitness-focused personality
4. Keep it concise but warm
5. If there were any errors or limitations, address them positively

## Guidelines:
- Use emojis appropriately (💪, 🏃‍♀️, 📊, etc.)
- Be encouraging and supportive
- End with a motivational or helpful note
- If multiple actions were taken, briefly summarize the key points

Generate only the final response - do not include explanations or meta-text.
"""

        # Get finalized response from LLM
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model=model_name,
            messages=[
                {"role": "system", "content": "You are Pili, a friendly and encouraging fitness chatbot."},
                {"role": "user", "content": finalization_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        finalized_response = completion.choices[0].message.content.strip()
        
        # Update the result with finalized response
        finalized_result = agent_result.copy()
        finalized_result["response"] = finalized_response
        finalized_result["original_response"] = original_response  # Keep original for debugging
        finalized_result["finalized"] = True
        
        return finalized_result
        
    except Exception as e:
        print(f"Finalization error: {e}")
        # Return original result if finalization fails
        fallback_result = agent_result.copy()
        fallback_result["finalization_error"] = str(e)
        return fallback_result


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
            # For streaming, get agent result first then stream it
            agent_result = await agent_system.process_request(
                request.user_id, 
                request.message
            )
            
            # Finalize the response with LLM
            finalized_result = await finalize_response(agent_result, request.message)
                  
            # Extract data for streaming
            response_text = finalized_result["response"]
            logs = finalized_result.get("logs", [])
            chain_of_thought = finalized_result.get("chain_of_thought", [])
            
            # Create streaming response
            async def create_agent_stream():
                # Create unique chat completion ID
                chat_id = f"chatcmpl-{int(time.time())}"
                created_time = int(time.time())
                
                # First chunk with metadata
                first_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": "pili-langgraph-swarm",
                    "choices": [{
                        "index": 0,
                        "delta": {"role": "assistant", "content": ""},
                        "finish_reason": None
                    }],
                    "metadata": {
                        "agent_system": "langgraph_swarm",
                        "chain_of_thought": chain_of_thought,
                        "logs": logs,
                        "finalized": finalized_result.get("finalized", False)
                    }
                }
                yield f"data: {json.dumps(first_chunk)}\n\n"
                
                # Stream the response content word by word
                words = response_text.split()
                for i, word in enumerate(words):
                    content = word if i == 0 else f" {word}"
                    chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": "pili-langgraph-swarm",
                        "choices": [{
                            "index": 0,
                            "delta": {"content": content},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.03)  # Small delay for smooth streaming
                
                # Final chunk
                final_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": "pili-langgraph-swarm",
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                create_agent_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        else:
            # Non-streaming response using agent system
            agent_result = await agent_system.process_request(
                request.user_id,
                request.message
            )
            
            # Finalize the response with LLM
            finalized_result = await finalize_response(agent_result, request.message)
            
            return ChatResponse(
                response=finalized_result["response"],
                logs=finalized_result["logs"]
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
                    "model": "pili-langgraph-swarm",
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
        # Test agent system processing
        result = await agent_system.process_request(request.user_id, request.message)
        
        # Apply finalization step
        finalized_result = await finalize_response(result, request.message)
        
        return {
            "agent_response": finalized_result["response"],
            "original_response": finalized_result.get("original_response", ""),
            "logs": finalized_result["logs"],
            "chain_of_thought": finalized_result.get("chain_of_thought", []),
            "finalized": finalized_result.get("finalized", False),
            "finalization_error": finalized_result.get("finalization_error"),
            "note": "Direct agent system testing with finalization"
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