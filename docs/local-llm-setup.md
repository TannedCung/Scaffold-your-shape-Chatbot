# Local LLM Setup Guide

Pili supports multiple LLM providers for intent detection and response generation. This guide shows how to set up local LLM providers as alternatives to OpenAI.

## Supported Providers

1. **OpenAI** (default) - Cloud-based
2. **Ollama** - Local LLM runner
3. **vLLM** - High-performance local inference
4. **Local/Custom** - Any OpenAI-compatible API

## Configuration

Set your LLM provider in `.env`:

```bash
LLM_PROVIDER=ollama  # or openai, vllm, local
```

## 1. Ollama Setup

Ollama is the easiest way to run local LLMs.

### Installation

```bash
# On macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com/download
```

### Usage

```bash
# Start Ollama
ollama serve

# Pull a model (in another terminal)
ollama pull llama2
# or
ollama pull mistral
ollama pull codellama
```

### Configuration

```bash
LLM_PROVIDER=ollama
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama2
LOCAL_LLM_API_KEY=  # Leave empty for Ollama
```

### Recommended Models for Pili

- `llama2` - Good general purpose
- `mistral` - Fast and capable
- `phi` - Lightweight option
- `llama2:13b` - Better performance (requires more RAM)

## 2. vLLM Setup

vLLM provides high-performance inference for local models.

### Installation

```bash
pip install vllm
```

### Usage

```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model microsoft/DialoGPT-medium \
    --port 8000
```

### Configuration

```bash
LLM_PROVIDER=vllm
LOCAL_LLM_BASE_URL=http://localhost:8000/v1
LOCAL_LLM_MODEL=microsoft/DialoGPT-medium
LOCAL_LLM_API_KEY=  # Usually not required
```

## 3. Custom/Local API

For any OpenAI-compatible API endpoint.

### Configuration

```bash
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://your-server:port/v1
LOCAL_LLM_MODEL=your-model-name
LOCAL_LLM_API_KEY=your-api-key-if-required
```

## Testing Your Setup

1. Start your LLM provider
2. Update your `.env` file
3. Restart Pili
4. Check the health endpoint:

```bash
curl http://localhost:8991/api/health
```

Look for the `llm_status` field in the response.

## Performance Tips

1. **Model Size**: Smaller models (7B parameters) work well for Pili's use case
2. **Memory**: Ensure you have enough RAM for your chosen model
3. **GPU**: Use GPU acceleration if available for better performance
4. **Fallback**: Pili will use rule-based intent detection if LLM fails

## Troubleshooting

### Common Issues

1. **Connection refused**: Make sure your LLM server is running
2. **Model not found**: Ensure the model is downloaded/available
3. **Memory errors**: Try a smaller model
4. **Slow responses**: Consider using GPU acceleration

### Logs

Check Pili's logs for LLM-related errors:

```bash
# LLM intent detection failed: Connection error
# LLM response generation failed: Model not found
```

### Health Check

Use the health endpoint to verify configuration:

```bash
curl http://localhost:8991/api/health | jq '.llm_status'
```

## Example Configurations

### Ollama with Mistral
```bash
LLM_PROVIDER=ollama
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=mistral
```

### vLLM with Llama2
```bash
LLM_PROVIDER=vllm
LOCAL_LLM_BASE_URL=http://localhost:8000/v1
LOCAL_LLM_MODEL=meta-llama/Llama-2-7b-chat-hf
```

### LMStudio (Local)
```bash
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://localhost:1234/v1
LOCAL_LLM_MODEL=local-model
``` 