# Docker Deployment Guide

This guide covers deploying the Pili Exercise Chatbot using Docker and Docker Compose with various configuration options.

## Quick Start

### 1. Basic Deployment with vLLM

```bash
# Clone the repository
git clone <repository-url>
cd Scaffold-you-shape-Chatbot

# Copy environment file
cp .env.sample .env

# Start the services
docker-compose up -d
```

### 2. Development Mode

```bash
# Start with development overrides (hot-reloading)
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

### 3. OpenAI Provider

```bash
# Set OpenAI API key in .env file
echo "OPENAI_API_KEY=your-api-key-here" >> .env

# Start with OpenAI provider
LLM_PROVIDER=openai docker-compose up -d pili-api redis
```

## Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   Pili API      │    │   vLLM/Ollama   │
│   (Optional)    │◄──►│   Port 8991     │◄──►│   Port 8000     │
│   Port 80/443   │    │                 │    │   Port 11434    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌─────────────────┐
                       │     Redis       │
                       │   Port 6379     │
                       └─────────────────┘
```

## Configuration Options

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Basic Configuration
ENVIRONMENT=production
LOG_LEVEL=info

# LLM Provider (choose one)
LLM_PROVIDER=vllm  # Options: openai, vllm, ollama

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo

# Local LLM Configuration (if using vLLM or Ollama)
LOCAL_LLM_BASE_URL=http://vllm-server:8000/v1
LOCAL_LLM_MODEL=microsoft/DialoGPT-medium
LOCAL_LLM_API_KEY=not-required

# Health Monitoring
HEALTH_CHECK_INTERVAL=30
```

### Docker Compose Profiles

The `docker-compose.yml` includes several optional services using profiles:

#### Standard Services (always started)
- `pili-api`: Main chatbot API
- `vllm-server`: Local LLM server
- `redis`: Caching and session management

#### Optional Services

**Nginx Reverse Proxy:**
```bash
docker-compose --profile nginx up -d
```

**Monitoring Stack:**
```bash
docker-compose --profile monitoring up -d
```

**All Services:**
```bash
docker-compose --profile nginx --profile monitoring up -d
```

## Deployment Scenarios

### 1. Minimal Deployment (API Only)

For testing or when using external LLM services:

```bash
# .env configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key

# Start only essential services
docker-compose up -d pili-api redis
```

**Access:**
- API: http://localhost:8991
- Documentation: http://localhost:8991/api/docs

### 2. Local LLM with vLLM

Full local deployment with vLLM:

```bash
# .env configuration
LLM_PROVIDER=vllm
LOCAL_LLM_BASE_URL=http://vllm-server:8000/v1
LOCAL_LLM_MODEL=microsoft/DialoGPT-medium

# Start with vLLM
docker-compose up -d
```

**Access:**
- Pili API: http://localhost:8991
- vLLM API: http://localhost:8000

### 3. Local LLM with Ollama

Alternative local deployment with Ollama:

```bash
# Modify docker-compose.yml to use ollama-server
# .env configuration
LLM_PROVIDER=ollama
LOCAL_LLM_BASE_URL=http://ollama-server:11434/v1
LOCAL_LLM_MODEL=llama2:7b-chat

# Start with Ollama
docker-compose up -d pili-api redis ollama-server
```

**Setup Ollama Model:**
```bash
# Pull model after startup
docker exec pili-ollama ollama pull llama2:7b-chat
```

### 4. Production with Nginx & Monitoring

Full production setup:

```bash
# .env configuration for production
ENVIRONMENT=production
LOG_LEVEL=warning
LLM_PROVIDER=vllm

# Start all services
docker-compose --profile nginx --profile monitoring up -d
```

**Access:**
- Main Site: http://localhost
- API: http://localhost/api
- Monitoring: http://localhost:3000 (Grafana)
- Metrics: http://localhost:9090 (Prometheus)

## GPU Support

### Enable GPU for vLLM

1. Install NVIDIA Container Toolkit
2. Uncomment GPU configuration in `docker-compose.yml`:

```yaml
vllm-server:
  # ... other config ...
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

3. Start services:
```bash
docker-compose up -d
```

## Storage & Persistence

### Volumes

The setup creates persistent volumes for:

- `vllm-cache`: HuggingFace model cache
- `ollama-data`: Ollama models and data
- `redis-data`: Redis persistence
- `prometheus-data`: Metrics data
- `grafana-data`: Dashboard configurations

### Backup

```bash
# Backup all volumes
docker run --rm -v pili_redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .

# Restore
docker run --rm -v pili_redis-data:/data -v $(pwd):/backup alpine tar xzf /backup/redis-backup.tar.gz -C /data
```

## Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' pili-chatbot
```

## Monitoring

### Built-in Health Endpoint

```bash
curl http://localhost:8991/api/health
```

### Prometheus Metrics

Available at `http://localhost:9090` when monitoring profile is enabled.

### Grafana Dashboard

Access at `http://localhost:3000` (admin/admin) with pre-configured dashboards.

## Scaling

### Horizontal Scaling

Scale the API service:

```bash
docker-compose up -d --scale pili-api=3
```

### Load Balancing

Use nginx profile for load balancing:

```yaml
# nginx.conf example
upstream pili_backend {
    server pili-api:8991;
    server pili-api:8991;
    server pili-api:8991;
}
```

## Troubleshooting

### Common Issues

1. **Port Conflicts:**
   ```bash
   # Check port usage
   docker-compose ps
   netstat -tulpn | grep :8991
   ```

2. **Memory Issues with vLLM:**
   ```bash
   # Monitor memory usage
   docker stats
   
   # Use smaller model in docker-compose.yml
   command: ["--model", "microsoft/DialoGPT-small"]
   ```

3. **Permission Issues:**
   ```bash
   # Fix log directory permissions
   sudo chown -R 1000:1000 logs/
   ```

### Logs

```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f pili-api

# View last 100 lines
docker-compose logs --tail=100 vllm-server
```

### Debug Mode

```bash
# Start in development mode with debugging
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

## Security Considerations

### Production Security

1. **Non-root User**: Container runs as non-root user `pili`
2. **Read-only Mounts**: Configuration files mounted read-only
3. **Network Isolation**: Services in isolated Docker network
4. **Health Checks**: Automatic restart on failures

### SSL Configuration

For HTTPS in production:

1. Place SSL certificates in `./ssl/` directory
2. Configure nginx with SSL in `nginx.conf`
3. Start with nginx profile

### Secrets Management

```bash
# Use Docker secrets for sensitive data
echo "your-openai-key" | docker secret create openai_key -

# Reference in docker-compose.yml
secrets:
  - openai_key
```

## Updates & Maintenance

### Update Images

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d
```

### Application Updates

```bash
# Rebuild application image
docker-compose build pili-api

# Restart application
docker-compose up -d pili-api
```

### Cleanup

```bash
# Remove stopped containers
docker-compose down

# Remove volumes (caution: data loss)
docker-compose down -v

# Clean up unused images
docker image prune
```

## Performance Tuning

### vLLM Optimization

```yaml
vllm-server:
  command: [
    "--model", "microsoft/DialoGPT-medium",
    "--tensor-parallel-size", "1",
    "--max-num-batched-tokens", "4096",
    "--max-model-len", "2048"
  ]
```

### API Optimization

```yaml
pili-api:
  command: [
    "uvicorn", "main:app",
    "--host", "0.0.0.0",
    "--port", "8991", 
    "--workers", "4",  # Increase workers for higher load
    "--worker-class", "uvicorn.workers.UvicornWorker"
  ]
```

This deployment setup provides a robust, scalable, and maintainable Docker-based deployment for the Pili Exercise Chatbot with multiple configuration options for different use cases. 