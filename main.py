from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse, StreamingResponse
from models.chat import ChatRequest, ChatResponse
from services.llm_service import llm_service
from core.chat_handler import chat_handler
import json
import time
import asyncio

app = FastAPI(
    title="Pili Exercise Chatbot API",
    description="A microservice chatbot named Pili for tracking exercises using LangGraph and FastAPI.",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs"
)

api_router = APIRouter(prefix="/api")

# Legacy streaming functions removed - now handled by orchestration agent

@api_router.post("/chat", tags=["Chatbot"])
async def chat_endpoint(request: ChatRequest):
    """
    Chat with Pili, the Exercise Tracker Bot.
    
    Supports both regular and streaming responses (set stream=true for streaming).
    Now includes conversation memory to maintain context across messages.
    
    Pili can help you with:
    - **Log exercises**: "I did 20 pushups"
    - **Track progress**: "Show my progress" 
    - **Join clubs**: "Join club fitness"
    - **Exit clubs**: "Leave club fitness"
    - **Get help**: "help"
    
    **Parameters:**
    - **user_id**: Unique user identifier
    - **message**: User's message to Pili
    - **stream**: Optional boolean to enable streaming response (default: false)
    """
    try:
        if request.stream:
            # For streaming, use orchestration agent but handle streaming manually
            # Get the orchestration result first
            orchestration_result = await chat_handler.orchestration_agent.process_request(
                request.user_id, 
                request.message
            )
            
            # Extract data for streaming
            response_text = orchestration_result["response"]
            logs = orchestration_result.get("logs", [])
            chain_of_thought = orchestration_result.get("chain_of_thought", [])
            
            # Create streaming response using orchestration result
            async def create_orchestration_stream():
                # Create unique chat completion ID
                chat_id = f"chatcmpl-{int(time.time())}"
                created_time = int(time.time())
                
                # First chunk with metadata
                first_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": "pili-orchestration",
                    "choices": [{
                        "index": 0,
                        "delta": {"role": "assistant", "content": ""},
                        "finish_reason": None
                    }],
                    "metadata": {
                        "orchestration_agent": "active",
                        "chain_of_thought": chain_of_thought,
                        "logs": logs
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
                        "model": "pili-orchestration",
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
                    "model": "pili-orchestration",
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                create_orchestration_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        else:
            # Use chat_handler for non-streaming response (with conversation memory)
            return await chat_handler.process_chat(request)
        
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
                    "model": "pili",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": "I'm sorry, something went wrong. Please try again."},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(error_stream(), media_type="text/plain")
        else:
            return ChatResponse(
                response="I'm sorry, something went wrong. Please try again.",
                logs=[{"error": str(e)}]
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
async def health_check():
    """Health check endpoint with LLM status."""
    llm_status = await llm_service.test_connection()
    
    return {
        "status": "healthy", 
        "service": "pili-exercise-chatbot",
        "llm_provider": llm_service.provider,
        "llm_model": llm_service.model,
        "llm_status": llm_status
    }

@app.post("/api/debug-llm")
async def debug_llm(request: ChatRequest):
    """Debug endpoint to test LLM response directly."""
    try:
        # Test intent detection
        intent_result = await llm_service.detect_intent(request.message)
        
        # Test response generation
        response = await llm_service.generate_response(
            intent_result.get("intent", "help"),
            request.message,
            "Debug test action result"
        )
        
        # Test thinking process extraction
        thinking, final_response = llm_service.extract_thinking_process(response)
        
        return {
            "raw_response": response,
            "thinking_process": thinking,
            "final_response": final_response,
            "intent_result": intent_result
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/chat-simple")
async def chat_simple(request: ChatRequest):
    """Simple chat endpoint without complex imports."""
    try:
        # Import here to avoid circular imports
        from services.llm_service import llm_service
        
        # Step 1: Detect intent
        intent_result = await llm_service.detect_intent(request.message)
        intent = intent_result.get("intent", "unknown")
        
        # Step 2: Simple action result based on intent
        if intent == "help":
            action_result = "I'm Pili! I can help you log activities, manage clubs, challenges, and track your progress."
        elif intent == "get_stats":
            action_result = "Here are your stats: You're doing great!"
        else:
            action_result = f"I detected intent '{intent}' for your message: {request.message}"
        
        # Step 3: Generate response (with timeout handling)
        try:
            final_response = await llm_service.generate_response(intent, request.message, action_result)
        except Exception as e:
            print(f"LLM failed: {e}")
            final_response = action_result
        
        return {
            "response": final_response,
            "logs": [{"intent": intent, "action_result": action_result}]
        }
        
    except Exception as e:
        return {"error": str(e)}

app.include_router(api_router) 