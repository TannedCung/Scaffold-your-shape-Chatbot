import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    langchain_api_key: str = ""
    langchain_project: str = "pili-exercise-chatbot"
    # Removed: exercise_service_url (now using MCP server integration)
    
    # LLM Configuration
    llm_provider: str = "openai"  # "openai", "ollama", "vllm", "local"
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    
    # Local LLM Configuration
    local_llm_base_url: str = "http://localhost:11434"  # Default Ollama URL
    local_llm_model: str = "llama2"  # Default local model
    local_llm_api_key: str = ""  # For vLLM or other services that require auth
    
    # MCP Server Configuration
    mcp_base_url: str = "http://localhost:3005/api/mcp"  # Scaffold Your Shape MCP server
    
    class Config:
        env_file = ".env"

settings = Settings() 