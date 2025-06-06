# Pili Chatbot Streaming API Documentation

The Pili chatbot now supports **streaming responses** similar to OpenAI's Chat Completion API, providing real-time response generation for a better user experience.

## Features

✅ **OpenAI-Compatible Format**: Server-Sent Events (SSE) with JSON chunks  
✅ **Real-time Streaming**: Responses are streamed word-by-word as they're generated  
✅ **Fallback Support**: Graceful fallback when LLM is unavailable  
✅ **Metadata Included**: Intent detection results included in first chunk  
✅ **Error Handling**: Robust error handling with streaming error responses  

## API Endpoints

### POST `/api/chat`

The main chat endpoint supports both regular and streaming responses.

**Request Body:**
```json
{
  "user_id": "string",
  "message": "string", 
  "stream": true  // Set to true for streaming response
}
```

**Parameters:**
- `user_id` (required): Unique identifier for the user
- `message` (required): The user's message to Pili
- `stream` (optional): Boolean flag to enable streaming (default: false)

## Streaming Response Format

When `stream: true` is set, the response follows OpenAI's Server-Sent Events format:

### Example Streaming Response

```
data: {"id": "chatcmpl-1749222763", "object": "chat.completion.chunk", "created": 1749222763, "model": "pili", "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": null}], "metadata": {"intent": "help", "confidence": 0.9, "extracted_info": {}, "llm_provider": "vllm"}}

data: {"id": "chatcmpl-1749222763", "object": "chat.completion.chunk", "created": 1749222763, "model": "pili", "choices": [{"index": 0, "delta": {"content": "Hi!"}, "finish_reason": null}]}

data: {"id": "chatcmpl-1749222763", "object": "chat.completion.chunk", "created": 1749222763, "model": "pili", "choices": [{"index": 0, "delta": {"content": " I'm"}, "finish_reason": null}]}

data: {"id": "chatcmpl-1749222763", "object": "chat.completion.chunk", "created": 1749222763, "model": "pili", "choices": [{"index": 0, "delta": {"content": " Pili"}, "finish_reason": null}]}

data: {"id": "chatcmpl-1749222763", "object": "chat.completion.chunk", "created": 1749222763, "model": "pili", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}

data: [DONE]
```

### Chunk Structure

Each chunk follows this structure:

```json
{
  "id": "chatcmpl-1749222763",           // Unique completion ID
  "object": "chat.completion.chunk",      // Object type
  "created": 1749222763,                  // Unix timestamp
  "model": "pili",                        // Model name
  "choices": [{
    "index": 0,                           // Choice index (always 0)
    "delta": {
      "content": "text chunk"             // Incremental content
    },
    "finish_reason": null                 // null until completion
  }],
  "metadata": {                           // Only in first chunk
    "intent": "help",                     // Detected intent
    "confidence": 0.9,                    // Intent confidence
    "extracted_info": {},                 // Extracted information
    "llm_provider": "vllm"               // LLM provider used
  }
}
```

### First Chunk (Metadata)

The first chunk includes additional metadata about the intent detection:
- `intent`: The detected user intent (help, log_activity, etc.)
- `confidence`: Confidence score for intent detection (0.0-1.0)
- `extracted_info`: Any extracted information from the message
- `llm_provider`: The LLM provider being used (openai, vllm, ollama, etc.)

### Content Chunks

Subsequent chunks contain incremental content in the `delta.content` field.

### Final Chunk

The last chunk has:
- Empty `delta` object
- `finish_reason: "stop"`

### Completion Signal

The stream ends with:
```
data: [DONE]
```

## Usage Examples

### 1. cURL Example

**Streaming Request:**
```bash
curl -X POST "http://localhost:8991/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "message": "help", "stream": true}' \
  --no-buffer
```

**Regular Request:**
```bash
curl -X POST "http://localhost:8991/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "message": "help", "stream": false}'
```

### 2. Python Example

```python
import asyncio
import aiohttp
import json

async def stream_chat():
    url = "http://localhost:8991/api/chat"
    payload = {
        "user_id": "user123",
        "message": "I ran 5km today!",
        "stream": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    
                    if data_str == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        
                        # Handle metadata (first chunk)
                        if 'metadata' in chunk:
                            metadata = chunk['metadata']
                            print(f"Intent: {metadata['intent']}")
                        
                        # Handle content chunks
                        if chunk.get('choices'):
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                print(delta['content'], end='', flush=True)
                                
                    except json.JSONDecodeError:
                        pass

asyncio.run(stream_chat())
```

### 3. JavaScript Example

```javascript
async function streamChat() {
  const response = await fetch('http://localhost:8991/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: 'user123',
      message: 'show my stats',
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        
        if (data === '[DONE]') {
          return;
        }

        try {
          const parsed = JSON.parse(data);
          
          // Handle metadata
          if (parsed.metadata) {
            console.log('Intent:', parsed.metadata.intent);
          }
          
          // Handle content
          if (parsed.choices?.[0]?.delta?.content) {
            process.stdout.write(parsed.choices[0].delta.content);
          }
        } catch (e) {
          // Skip malformed JSON
        }
      }
    }
  }
}
```

## Error Handling

### Streaming Errors

If an error occurs during streaming, an error chunk is sent:

```json
{
  "id": "chatcmpl-error-1749222763",
  "object": "chat.completion.chunk", 
  "created": 1749222763,
  "model": "pili",
  "choices": [{
    "index": 0,
    "delta": {"content": "I'm sorry, something went wrong. Please try again."},
    "finish_reason": "stop"
  }]
}
```

### Fallback Behavior

- **LLM Unavailable**: Falls back to rule-based intent detection and pre-defined responses
- **Streaming Issues**: Falls back to word-by-word streaming of action results
- **Timeout**: Graceful timeout handling with fallback responses

## Performance

- **Streaming Delay**: Small 10ms delay between chunks for smooth UX
- **Timeout**: 80-second timeout for LLM response generation
- **Buffer Size**: Optimized for real-time feel while maintaining reliability

## Supported Intents

The streaming API supports all Pili intents:

- `help`: Get help and available commands
- `log_activity`: Log fitness activities
- `manage_clubs`: Create, join, or find fitness clubs  
- `manage_challenges`: Create, join, or view challenges
- `get_stats`: View fitness statistics and progress
- `unknown`: Handle unrecognized messages

## Headers

For streaming responses, these headers are set:

```
Cache-Control: no-cache
Connection: keep-alive
Content-Type: text/plain; charset=utf-8
```

## Integration Notes

- **OpenAI Compatible**: Can be used as a drop-in replacement for OpenAI's streaming API in many cases
- **Real-time UI**: Perfect for chat interfaces that show typing indicators
- **Progressive Enhancement**: Gracefully degrades to regular responses if streaming fails
- **Stateless**: Each request is independent, no session management required

## Testing

Use the included `test_streaming.py` script to test both streaming and regular responses:

```bash
python test_streaming.py
```

This provides a comprehensive test of the streaming functionality with proper error handling and demonstration of the expected output format. 