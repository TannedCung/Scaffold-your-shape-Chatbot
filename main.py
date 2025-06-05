from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse
from models.chat import ChatRequest, ChatResponse
from core.chat_handler import chat_handler
from services.llm_service import llm_service

app = FastAPI(
    title="Pili Exercise Chatbot API",
    description="A microservice chatbot named Pili for tracking exercises using LangGraph and FastAPI.",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs"
)

api_router = APIRouter(prefix="/api")

@api_router.post("/chat", response_model=ChatResponse, tags=["Chatbot"])
async def chat_endpoint(request: ChatRequest):
    """
    Chat with Pili, the Exercise Tracker Bot.
    
    Pili can help you with:
    - **Log exercises**: "I did 20 pushups"
    - **Track progress**: "Show my progress" 
    - **Join clubs**: "Join club fitness"
    - **Exit clubs**: "Leave club fitness"
    - **Get help**: "help"
    
    **Parameters:**
    - **user_id**: Unique user identifier
    - **message**: User's message to Pili
    """
    return await chat_handler.process_chat(request)

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

app.include_router(api_router) 