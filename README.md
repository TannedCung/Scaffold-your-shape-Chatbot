# Exercise Tracker Chatbot Microservice

This is a chatbot microservice for an exercise tracker application, built with FastAPI and LangGraph.

## Features
- Log exercises via chat
- Query exercise progress
- Simple intent recognition using LangGraph
- Interactive API docs (Swagger) at `/api/docs`

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Access the API docs:**
   - Open [http://localhost:8000/api/docs](http://localhost:8000/api/docs) in your browser.

## API Endpoints

### POST `/api/chat`
Chat with the Exercise Tracker Bot.

**Request Body:**
```
{
  "user_id": "string",
  "message": "string"
}
```

**Response:**
```
{
  "response": "string",
  "logs": [
    { "user_id": "string", "entry": "string" }
  ]
}
```

### GET `/api/docs`
Redirects to the Swagger UI documentation.

---

## License
MIT
