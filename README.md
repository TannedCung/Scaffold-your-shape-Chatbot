# Exercise Tracker Chatbot Microservice

A sophisticated chatbot microservice for an exercise tracker application, built with FastAPI, LangGraph, and LangSmith. Features a multiagent architecture with structured tools and services.

## 🏗️ Architecture

```
├── agents/           # LangGraph-based agent implementations
├── tools/            # Agent tools for exercise tracking
├── services/         # External service integrations
├── models/           # Pydantic data models
├── config/           # Configuration and settings
├── core/             # Core business logic
└── main.py           # FastAPI application entry point
```

## 🚀 Features

- **Multiagent Architecture**: LangGraph-powered conversation flow
- **Exercise Logging**: Natural language exercise tracking
- **Club Management**: Join/exit fitness clubs and challenges
- **Progress Tracking**: View exercise history and statistics
- **External Service Integration**: Connect to exercise tracking APIs
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
- `LANGCHAIN_PROJECT`: Project name for LangSmith tracking
- `EXERCISE_SERVICE_URL`: External exercise service API endpoint

## 📝 API Endpoints

### POST `/api/chat`
Main chat endpoint for interacting with the bot.

**Request:**
```json
{
  "user_id": "user123",
  "message": "I did 20 pushups"
}
```

**Response:**
```json
{
  "response": "Exercise logged successfully! pushup - 20 reps",
  "logs": [...]
}
```

### GET `/api/health`
Health check endpoint.

### GET `/api/docs`
Redirects to Swagger UI documentation.

## 🤖 Supported Commands

| Intent | Example Messages | Description |
|--------|------------------|-------------|
| Log Exercise | "I did 20 pushups", "Completed 5k run" | Track exercise activities |
| Club Management | "Join club fitness", "Leave club running" | Manage club memberships |
| Progress Tracking | "Show my progress", "What are my stats?" | View exercise history |
| Help | "help", "what can you do?" | Get available commands |

## 🧠 Agent Architecture

The chatbot uses a LangGraph-based multiagent system:

1. **Intent Detection**: Analyzes user input to determine action
2. **Tool Selection**: Routes to appropriate exercise tracking tools
3. **External Integration**: Communicates with exercise service APIs
4. **Response Generation**: Formats and returns user-friendly responses

## 🔌 External Service Integration

The microservice can integrate with external exercise tracking APIs. Configure the `EXERCISE_SERVICE_URL` to connect to your exercise tracking backend.

Expected API endpoints:
- `POST /exercises` - Log exercise activities
- `GET /users/{user_id}/progress` - Get user progress
- `POST /clubs/{club_id}/members` - Join club
- `DELETE /clubs/{club_id}/members` - Leave club

## 📊 LangSmith Integration

Monitor and analyze chatbot conversations using LangSmith:
- Conversation flow tracking
- Performance analytics
- User interaction insights

## 🧪 Development

The project follows a modular architecture for easy extension:

- Add new tools in `tools/`
- Create new agents in `agents/`
- Extend services in `services/`
- Add models in `models/`

## 📄 License

MIT License
