# Pili - Exercise Tracker Chatbot Microservice

A sophisticated chatbot microservice named **Pili** for an exercise tracker application, built with FastAPI, LangGraph, and LangSmith. Features a multiagent architecture with comprehensive API integration for the Scaffold Your Shape fitness platform.

## 🏗️ Architecture

```
├── agents/           # LangGraph-based agent implementations (Pili)
├── tools/            # API tools for fitness tracking integration
├── services/         # External API service integrations
├── models/           # Pydantic data models for API and chat
├── config/           # Configuration and settings
├── core/             # Core business logic and chat handling
└── main.py           # FastAPI application entry point
```

## 🚀 Features

- **Pili AI Assistant**: Natural language fitness companion
- **Comprehensive Activity Logging**: Track running, cycling, swimming, yoga, and more
- **Club Management**: Create, join, and discover fitness clubs
- **Challenge System**: Create and participate in fitness challenges
- **Progress Tracking**: Detailed statistics and workout history
- **API Integration**: Full integration with Scaffold Your Shape API
- **LangSmith Integration**: Conversation monitoring and analytics
- **Auto-generated API Documentation**: Interactive Swagger UI

## 🛠️ Setup

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd exercise-tracker-chatbot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.sample .env
   # Edit .env with your actual values
   ```

4. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Access the API docs:**
   - Open [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

## 🔧 Configuration

Set the following environment variables in your `.env` file:

- `LANGCHAIN_API_KEY`: Your LangChain API key for LangSmith
- `LANGCHAIN_PROJECT`: Project name for LangSmith tracking (default: pili-exercise-chatbot)
- `EXERCISE_SERVICE_URL`: Scaffold Your Shape API endpoint (e.g., http://localhost:3001/api)

## 📝 API Endpoints

### POST `/api/chat`
Main chat endpoint for interacting with Pili.

**Request:**
```json
{
  "user_id": "user123",
  "message": "I ran 5 km in 30 minutes today"
}
```

**Response:**
```json
{
  "response": "Great job! I've logged your Running activity - 5.0 km, 30 minutes.",
  "logs": []
}
```

### GET `/api/health`
Health check endpoint.

### GET `/api/docs`
Redirects to Swagger UI documentation.

## 🤖 What Pili Can Do

| Category | Example Messages | Pili's Capabilities |
|----------|------------------|-------------------|
| **Activity Logging** | "I ran 5 km", "Did yoga for 45 minutes", "Cycled 15 km at the park" | Automatically extracts activity type, distance, duration, and location |
| **Club Management** | "Show me clubs", "Create club runners for marathon training" | Search, create, and manage fitness clubs |
| **Challenges** | "Show challenges", "Create marathon challenge for 42 km" | Participate in and create fitness challenges |
| **Progress Tracking** | "Show my stats", "What's my progress?" | View comprehensive fitness statistics |
| **Help & Guidance** | "help", "what can you do?" | Get assistance and discover features |

## 🧠 Pili's Intelligence

Pili uses advanced natural language processing to:

1. **Smart Activity Parsing**: Understands various ways to describe workouts
   - "I ran 3 miles" → Converts to kilometers and logs properly
   - "30 minute bike ride at Central Park" → Extracts duration, activity, and location

2. **Context-Aware Responses**: Provides personalized feedback based on user history

3. **Multi-Intent Handling**: Can process complex requests like "Show my running stats from this month"

## 🔌 Scaffold Your Shape API Integration

Pili integrates seamlessly with the Scaffold Your Shape platform:

**Activities Endpoint**: `POST /activities`
- Logs workouts with full activity details
- Supports all activity types (running, cycling, swimming, etc.)

**Clubs Endpoint**: `GET/POST /clubs`
- Browse and create fitness communities
- Join clubs with shared interests

**Challenges Endpoint**: `GET/POST /challenges`
- Participate in fitness challenges
- Create custom challenges with targets and timelines

**Authentication**: Session-based authentication using NextAuth.js tokens

## 📊 LangSmith Integration

Monitor Pili's conversations and performance:
- Intent detection accuracy
- User interaction patterns
- Response quality metrics
- Conversation flow analysis

## 🧪 Development

The project follows a modular architecture for easy extension:

**Adding New Tools:**
```python
# In tools/api_tools.py
async def new_tool(user_id: str, message: str) -> str:
    # Your tool logic here
    return response
```

**Adding New Intents:**
```python
# In agents/pili_agent.py
def detect_intent(state: PiliAgentState) -> str:
    # Add new intent detection logic
    if "new_intent_keyword" in message:
        state.intent = "new_intent"
```

## 📄 License

MIT License

---

**Meet Pili** - Your friendly AI fitness companion that makes tracking workouts as easy as having a conversation! 🏃‍♀️💪
