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

class StreamingResponseWithMemory:
    """A streaming response wrapper that saves conversation to memory after completion."""
    
    def __init__(self, user_id: str, stream_generator, message: str):
        self.user_id = user_id
        self.stream_generator = stream_generator
        self.message = message
        self.accumulated_response = ""
    
    async def __aiter__(self):
        try:
            async for chunk in self.stream_generator:
                # Extract content from the chunk if it's a data line
                if chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
                    try:
                        chunk_data = json.loads(chunk[6:])  # Remove "data: " prefix
                        if "choices" in chunk_data and chunk_data["choices"]:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta:
                                self.accumulated_response += delta["content"]
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass  # Skip chunks that don't contain content
                
                yield chunk
        finally:
            # Save the complete response to memory after streaming
            try:
                if self.accumulated_response.strip():  # Only save if there's actual content
                    memory = chat_handler.get_or_create_memory(self.user_id)
                    memory.chat_memory.add_ai_message(self.accumulated_response)
            except Exception as e:
                print(f"Error saving AI response to memory: {e}")

async def create_stream_response_with_memory(user_id: str, message: str, intent: str, confidence: float, extracted_info: dict, action_result: str, conversation_history: list = None):
    """Create a streaming response and save it to memory after completion."""
    
    # Create unique chat completion ID
    chat_id = f"chatcmpl-{int(time.time())}"
    created_time = int(time.time())
    
    # Variable to accumulate the response content for saving to memory
    accumulated_response = ""
    
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
            "llm_provider": llm_service.provider,
            "conversation_length": len(conversation_history) if conversation_history else 0
        }
    }
    yield f"data: {json.dumps(first_chunk)}\n\n"
    
    # Stream the response content
    try:
        async for content_chunk in llm_service.generate_response_stream(intent, message, action_result, conversation_history):
            accumulated_response += content_chunk
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
            accumulated_response += content
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
    
    # Note: Memory saving needs to be handled by the caller since this is a generator

async def create_stream_response(user_id: str, message: str, intent: str, confidence: float, extracted_info: dict, action_result: str, conversation_history: list = None):
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
            "llm_provider": llm_service.provider,
            "conversation_length": len(conversation_history) if conversation_history else 0
        }
    }
    yield f"data: {json.dumps(first_chunk)}\n\n"
    
    # Stream the response content
    try:
        async for content_chunk in llm_service.generate_response_stream(intent, message, action_result, conversation_history):
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
            # For streaming, we need to handle the conversation memory manually
            # Get user's conversation memory
            memory = chat_handler.get_or_create_memory(request.user_id)
            conversation_history = memory.chat_memory.messages
            
            # Step 1: Detect intent with conversation context
            try:
                intent_result = await llm_service.detect_intent(request.message, conversation_history)
                intent = intent_result.get("intent", "unknown")
                confidence = intent_result.get("confidence", 0.5)
                extracted_info = intent_result.get("extracted_info", {})
            except Exception as e:
                print(f"Intent detection failed, using fallback: {e}")
                fallback_result = llm_service._fallback_intent_detection(request.message)
                intent = fallback_result.get("intent", "unknown")
                confidence = fallback_result.get("confidence", 0.5)
                extracted_info = fallback_result.get("extracted_info", {})
            
            # Step 2: Handle the intent (using the same logic as chat_handler)
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
            
            # Save the conversation to memory (before streaming starts)
            memory.chat_memory.add_user_message(request.message)
            
            # Create the streaming generator
            stream_generator = create_stream_response_with_memory(
                request.user_id, request.message, intent, confidence, extracted_info, action_result, conversation_history
            )
            
            # Wrap with memory-saving functionality
            memory_stream = StreamingResponseWithMemory(request.user_id, stream_generator, request.message)
            
            return StreamingResponse(
                memory_stream,
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