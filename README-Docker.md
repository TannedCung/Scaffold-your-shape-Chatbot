# Pili Chatbot - Docker Quick Start

This README provides quick Docker setup instructions for the Pili Exercise Chatbot.

## 🚀 Quick Start

### Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- 4GB+ RAM (for local LLM)
- Optional: NVIDIA GPU + Container Toolkit (for GPU acceleration)

### 1. Basic Setup

```bash
# Clone repository
git clone <your-repo-url>
cd Scaffold-you-shape-Chatbot

# Copy environment template
cp .env.sample .env

# Start with default settings (vLLM)
docker-compose up -d

# Check health
curl http://localhost:8991/api/health
```

### 2. Test the API

```bash
# Test chat endpoint
curl -X POST "http://localhost:8991/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "help"}'

# Test streaming
curl -X POST "http://localhost:8991/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "help", "stream": true}' \
  --no-buffer
```

## 🔧 Configuration Options

### LLM Providers

#### Option 1: OpenAI (Recommended for production)
```bash
# Edit .env file
echo "LLM_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=your-key-here" >> .env

# Start only API and Redis
docker-compose up -d pili-api redis
```

#### Option 2: Local vLLM (Default)
```bash
# Uses included vLLM server
docker-compose up -d
```

#### Option 3: Ollama
```bash
# Start Ollama server
docker-compose up -d pili-api redis ollama-server

# Pull model
docker exec pili-ollama ollama pull llama2:7b-chat

# Update .env
echo "LLM_PROVIDER=ollama" >> .env
echo "LOCAL_LLM_BASE_URL=http://ollama-server:11434/v1" >> .env
```

## 📊 Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Pili API | 8991 | Main chatbot API |
| vLLM | 8000 | Local LLM server |
| Ollama | 11434 | Alternative LLM server |
| Redis | 6379 | Cache/sessions |
| Nginx | 80/443 | Reverse proxy (optional) |
| Grafana | 3000 | Monitoring (optional) |
| Prometheus | 9090 | Metrics (optional) |

## 🛠️ Common Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f pili-api

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build pili-api
docker-compose up -d pili-api

# Scale API instances
docker-compose up -d --scale pili-api=3

# Clean up
docker-compose down -v  # ⚠️ Removes data volumes
```

## 🔍 Development Mode

```bash
# Start with hot-reloading
docker-compose -f docker-compose.yml -f docker-compose.override.yml up

# This enables:
# - Code hot-reloading
# - Debug logs
# - Smaller LLM model
# - Debug port 5678
```

## 📈 Production Setup

```bash
# Full production with monitoring
docker-compose --profile nginx --profile monitoring up -d

# Access points:
# - API: http://localhost/api
# - Docs: http://localhost/api/docs
# - Monitoring: http://localhost:3000
```

## 🔧 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   lsof -i :8991
   
   # Change port in docker-compose.yml
   ports:
     - "8992:8991"  # Use 8992 instead
   ```

2. **Out of memory with vLLM**
   ```bash
   # Use smaller model
   # Edit docker-compose.yml:
   command: ["--model", "microsoft/DialoGPT-small"]
   ```

3. **Permission errors**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER logs/ data/
   ```

### Health Checks

```bash
# Check all services
docker-compose ps

# Detailed health
docker inspect --format='{{json .State.Health}}' pili-chatbot | jq

# Test endpoints
curl http://localhost:8991/api/health
curl http://localhost:8000/health  # vLLM
```

### Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs pili-api

# Follow logs
docker-compose logs -f --tail=100 pili-api

# Error logs only
docker-compose logs | grep ERROR
```

## 🔒 Security Notes

- Container runs as non-root user
- Secrets mounted read-only
- Network isolation enabled
- Rate limiting with nginx profile
- Health checks for auto-recovery

## 📦 Data Persistence

Data is persisted in Docker volumes:
- `redis-data`: User sessions and cache
- `vllm-cache`: Downloaded models
- `ollama-data`: Ollama models
- `logs/`: Application logs (host mount)

## 🎯 API Usage Examples

### Basic Chat
```bash
curl -X POST "http://localhost:8991/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "I ran 5km today!"
  }'
```

### Streaming Chat
```bash
curl -X POST "http://localhost:8991/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123", 
    "message": "Show my progress",
    "stream": true
  }' --no-buffer
```

### Different Intents
```bash
# Activity logging
curl -X POST "http://localhost:8991/api/chat" \
  -d '{"user_id": "user123", "message": "I did 50 pushups"}'

# Get help
curl -X POST "http://localhost:8991/api/chat" \
  -d '{"user_id": "user123", "message": "help"}'

# Stats
curl -X POST "http://localhost:8991/api/chat" \
  -d '{"user_id": "user123", "message": "show my stats"}'
```

## 🚀 Next Steps

1. **API Integration**: See `docs/streaming-api.md` for detailed API documentation
2. **Deployment**: Check `docs/docker-deployment.md` for production deployment
3. **Local LLM**: Review `docs/local-llm-setup.md` for LLM configuration
4. **Monitoring**: Set up Grafana dashboards for production monitoring

## 📞 Support

- View logs: `docker-compose logs pili-api`
- Health check: `curl http://localhost:8991/api/health`
- API docs: `http://localhost:8991/api/docs`

Ready to chat with Pili! 🏃‍♀️💪 