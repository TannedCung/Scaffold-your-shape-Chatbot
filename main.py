from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse, StreamingResponse
from models.chat import ChatRequest, ChatResponse
from services.llm_service import llm_service
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

async def create_stream_response(user_id: str, message: str, intent: str, confidence: float, extracted_info: dict, action_result: str):
    """Create a streaming response similar to OpenAI's format."""
    
    # Create unique chat completion ID
    chat_id = f"chatcmpl-{int(time.time())}"
    created_time = int(time.time())
    
    # First chunk - send the intent and metadata
    first_chunk = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created_time,
        "model": "pili",
        "choices": [{
            "index": 0,
            "delta": {"role": "assistant", "content": ""},
            "finish_reason": None
        }],
        "metadata": {
            "intent": intent,
            "confidence": confidence,
            "extracted_info": extracted_info,
            "llm_provider": llm_service.provider
        }
    }
    yield f"data: {json.dumps(first_chunk)}\n\n"
    
    # Stream the response content
    try:
        async for content_chunk in llm_service.generate_response_stream(intent, message, action_result):
            chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk", 
                "created": created_time,
                "model": "pili",
                "choices": [{
                    "index": 0,
                    "delta": {"content": content_chunk},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.01)  # Small delay for smoother streaming
    except Exception as e:
        print(f"Streaming error: {e}")
        # Fallback: send action result as chunks
        words = action_result.split()
        for i, word in enumerate(words):
            content = word if i == 0 else f" {word}"
            chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": "pili",
                "choices": [{
                    "index": 0,
                    "delta": {"content": content},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.05)
    
    # Final chunk - indicate completion
    final_chunk = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created_time,
        "model": "pili",
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"

@api_router.post("/chat", tags=["Chatbot"])
async def chat_endpoint(request: ChatRequest):
    """
    Chat with Pili, the Exercise Tracker Bot.
    
    Supports both regular and streaming responses (set stream=true for streaming).
    
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
        # Step 1: Detect intent with fallback
        try:
            intent_result = await llm_service.detect_intent(request.message)
            intent = intent_result.get("intent", "unknown")
            confidence = intent_result.get("confidence", 0.5)
            extracted_info = intent_result.get("extracted_info", {})
        except Exception as e:
            print(f"Intent detection failed, using fallback: {e}")
            # Fallback to rule-based detection
            fallback_result = llm_service._fallback_intent_detection(request.message)
            intent = fallback_result.get("intent", "unknown")
            confidence = fallback_result.get("confidence", 0.5)
            extracted_info = fallback_result.get("extracted_info", {})
        
        # Step 2: Handle the intent
        action_result = ""
        if intent == "log_activity":
            action_result = "Great job! I've logged your activity for you."
        elif intent == "manage_clubs":
            action_result = "Here are the clubs I found for you!"
        elif intent == "manage_challenges":
            action_result = "Here are some exciting challenges for you!"
        elif intent == "get_stats":
            action_result = "Your stats look amazing! Keep up the great work!"
        elif intent == "help":
            action_result = (
                "Hi! I'm Pili, your fitness companion! 🏃‍♀️ Here's what I can help you with:\n\n"
                "📝 **Log Activities:**\n"
                "• 'I ran 5 km in 30 minutes'\n"
                "• 'Did 45 minutes of yoga'\n"
                "• 'Cycled 15 km at the park'\n\n"
                "👥 **Club Management:**\n"
                "• 'Show me clubs' or 'Find running clubs'\n"
                "• 'Create club runners for people who love running'\n\n"
                "🏆 **Challenges:**\n"
                "• 'Show challenges' or 'Find running challenges'\n"
                "• 'Create marathon challenge for 42 km'\n\n"
                "📊 **Track Progress:**\n"
                "• 'Show my stats' or 'My progress'\n"
                "• 'How many activities have I logged?'\n\n"
                "Just tell me what you want to do in natural language!"
            )
        else:
            action_result = (
                "I'm Pili, and I didn't quite catch that! 🤔 I can help you with:\n"
                "• Logging workouts and activities\n"
                "• Finding and creating fitness clubs\n"
                "• Managing fitness challenges\n"
                "• Tracking your progress\n\n"
                "Try saying something like 'I ran 3 miles' or 'Show my stats' or just type 'help' for more examples!"
            )
        
        # Step 3: Return streaming or regular response based on request
        if request.stream:
            return StreamingResponse(
                create_stream_response(request.user_id, request.message, intent, confidence, extracted_info, action_result),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        else:
            # Regular non-streaming response
            try:
                final_response = await llm_service.generate_response(intent, request.message, action_result)
            except Exception as e:
                print(f"LLM response generation failed, using action result: {e}")
                final_response = action_result
            
            # Create logs
            logs = [{
                "intent": intent,
                "confidence": confidence,
                "extracted_info": extracted_info,
                "action_result": action_result,
                "llm_provider": llm_service.provider
            }]
            
            return ChatResponse(response=final_response, logs=logs)
        
    except Exception as e:
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