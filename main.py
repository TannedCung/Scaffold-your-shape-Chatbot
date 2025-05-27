from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse
from models.chat import ChatRequest, ChatResponse
from core.chat_handler import chat_handler

app = FastAPI(
    title="Exercise Tracker Chatbot API",
    description="A microservice chatbot for tracking exercises using LangGraph and FastAPI.",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs"
)

api_router = APIRouter(prefix="/api")

@api_router.post("/chat", response_model=ChatResponse, tags=["Chatbot"])
async def chat_endpoint(request: ChatRequest):
    """
    Chat with the Exercise Tracker Bot.
    
    The bot can help you with:
    - **Log exercises**: "I did 20 pushups"
    - **Track progress**: "Show my progress" 
    - **Join clubs**: "Join club fitness"
    - **Exit clubs**: "Leave club fitness"
    - **Get help**: "help"
    
    **Parameters:**
    - **user_id**: Unique user identifier
    - **message**: User's message to the bot
    """
    return await chat_handler.process_chat(request)

@api_router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "exercise-tracker-chatbot"}

@api_router.get("/docs", include_in_schema=False)
async def custom_docs_redirect():
    """Redirect to the FastAPI Swagger UI documentation."""
    return RedirectResponse(url="/api/docs")

@app.get("/", include_in_schema=False)
async def root():
    """Redirect to the API docs."""
    return RedirectResponse(url="/api/docs")

app.include_router(api_router) 