import os
from typing import Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from langchain_core.runnables import RunnableConfig


class Configuration(BaseModel):
    """The configurable fields for Pili fitness chatbot."""

    # LangChain Configuration
    langchain_api_key: str = Field(
        default="",
        title="LangChain API Key",
        description="API key for LangSmith tracing and monitoring"
    )
    
    langchain_project: str = Field(
        default="pili-exercise-chatbot",
        title="LangChain Project",
        description="Project name for LangSmith"
    )

    # LLM Configuration
    llm_provider: str = Field(
        default="openai",
        title="LLM Provider",
        description="LLM provider to use: openai, ollama, vllm, local"
    )
    
    openai_api_key: str = Field(
        default="",
        title="OpenAI API Key",
        description="API key for OpenAI services"
    )
    
    openai_model: str = Field(
        default="gpt-3.5-turbo",
        title="OpenAI Model",
        description="OpenAI model to use for completions"
    )

    # Local LLM Configuration
    local_llm_base_url: str = Field(
        default="http://localhost:11434",
        title="Local LLM Base URL",
        description="Base URL for local LLM service (Ollama, vLLM, etc.)"
    )
    
    local_llm_model: str = Field(
        default="llama2",
        title="Local LLM Model",
        description="Local model name to use"
    )
    
    local_llm_api_key: str = Field(
        default="",
        title="Local LLM API Key",
        description="API key for local LLM services that require authentication"
    )

    # MCP Server Configuration
    mcp_base_url: str = Field(
        default="http://localhost:3005/api/mcp",
        title="MCP Base URL",
        description="Base URL for Scaffold Your Shape MCP server"
    )

    # Agent Configuration
    max_conversation_history: int = Field(
        default=20,
        title="Max Conversation History",
        description="Maximum number of messages to keep in conversation history"
    )
    
    agent_timeout: float = Field(
        default=30.0,
        title="Agent Timeout",
        description="Timeout in seconds for agent operations"
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)


class Settings(BaseSettings):
    """Settings using pydantic-settings for environment variable loading."""
    
    # LangChain Configuration
    langchain_api_key: str = ""
    langchain_project: str = "pili-exercise-chatbot"
    
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
    
    # Agent Configuration
    max_conversation_history: int = 20
    agent_timeout: float = 30.0
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()


def get_configuration() -> Configuration:
    """Get configuration instance from current settings."""
    return Configuration(
        langchain_api_key=settings.langchain_api_key,
        langchain_project=settings.langchain_project,
        llm_provider=settings.llm_provider,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
        local_llm_base_url=settings.local_llm_base_url,
        local_llm_model=settings.local_llm_model,
        local_llm_api_key=settings.local_llm_api_key,
        mcp_base_url=settings.mcp_base_url,
        max_conversation_history=settings.max_conversation_history,
        agent_timeout=settings.agent_timeout
    ) 