Configuration Guide
===================

This guide covers all configuration options for Pili, the Exercise Tracker Chatbot.

Environment Variables
=====================

Pili uses environment variables for configuration. Create a ``.env`` file in the project root:

.. code-block:: bash

   # Copy the sample environment file
   cp .env.sample .env

Core Configuration
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Variable
     - Required
     - Description
   * - ``LANGCHAIN_API_KEY``
     - Yes
     - Your LangChain API key for LangSmith integration
   * - ``LANGCHAIN_PROJECT``
     - No
     - Project name for LangSmith (default: "pili-exercise-chatbot")
   * - ``LLM_PROVIDER``
     - Yes
     - LLM provider: "openai", "ollama", "vllm", or "local"

LLM Provider Configuration
--------------------------

**OpenAI Configuration**

.. code-block:: bash

   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-openai-api-key-here
   OPENAI_MODEL=gpt-4  # Optional: default is gpt-3.5-turbo

**Local LLM Configuration**

.. code-block:: bash

   LLM_PROVIDER=local
   LOCAL_LLM_BASE_URL=http://localhost:11434
   LOCAL_LLM_MODEL=llama2
   LOCAL_LLM_TIMEOUT=60  # Optional: request timeout in seconds

**Ollama Configuration**

.. code-block:: bash

   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2

**VLLM Configuration**

.. code-block:: bash

   LLM_PROVIDER=vllm
   VLLM_BASE_URL=http://localhost:8000
   VLLM_MODEL=meta-llama/Llama-2-7b-chat-hf

MCP Server Configuration
------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Variable
     - Required
     - Description
   * - ``MCP_BASE_URL``
     - Yes
     - URL of the Scaffold Your Shape MCP server
   * - ``MCP_TIMEOUT``
     - No
     - Request timeout in seconds (default: 30)
   * - ``MCP_RETRY_ATTEMPTS``
     - No
     - Number of retry attempts (default: 3)

.. code-block:: bash

   # MCP Server Settings
   MCP_BASE_URL=http://192.168.1.98:3005/api/mcp
   MCP_TIMEOUT=30
   MCP_RETRY_ATTEMPTS=3

Memory Configuration
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Variable
     - Required
     - Description
   * - ``MEMORY_TYPE``
     - No
     - Memory type: "buffer", "summary", "entity" (default: "buffer")
   * - ``MEMORY_MAX_TOKENS``
     - No
     - Maximum tokens to store in memory (default: 2000)
   * - ``MEMORY_RETURN_MESSAGES``
     - No
     - Number of messages to return (default: 20)

.. code-block:: bash

   # Memory Settings
   MEMORY_TYPE=buffer
   MEMORY_MAX_TOKENS=2000
   MEMORY_RETURN_MESSAGES=20

Application Configuration
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Variable
     - Required
     - Description
   * - ``APP_HOST``
     - No
     - Host to bind the server (default: "0.0.0.0")
   * - ``APP_PORT``
     - No
     - Port to bind the server (default: 8000)
   * - ``LOG_LEVEL``
     - No
     - Logging level: "DEBUG", "INFO", "WARNING", "ERROR" (default: "INFO")
   * - ``CORS_ORIGINS``
     - No
     - Comma-separated list of allowed CORS origins

.. code-block:: bash

   # Application Settings
   APP_HOST=0.0.0.0
   APP_PORT=8000
   LOG_LEVEL=INFO
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001

Configuration Files
===================

In addition to environment variables, Pili uses several configuration files:

Settings Module
---------------

The main configuration is handled by ``config/settings.py``:

.. code-block:: python

   from pydantic_settings import BaseSettings
   from typing import Optional, List

   class Settings(BaseSettings):
       # LangChain Configuration
       langchain_api_key: str
       langchain_project: str = "pili-exercise-chatbot"
       
       # LLM Configuration
       llm_provider: str = "openai"
       openai_api_key: Optional[str] = None
       
       # MCP Configuration
       mcp_base_url: str = "http://192.168.1.98:3005/api/mcp"
       
       class Config:
           env_file = ".env"

Agent Configuration
-------------------

Agent-specific settings can be configured in ``agents/prompts.py``:

.. code-block:: python

   # Orchestration Agent Settings
   ORCHESTRATION_TEMPERATURE = 0.3
   ORCHESTRATION_MAX_TOKENS = 500

   # Logger Agent Settings  
   LOGGER_TEMPERATURE = 0.1
   LOGGER_MAX_TOKENS = 300

   # Coach Agent Settings
   COACH_TEMPERATURE = 0.7
   COACH_MAX_TOKENS = 800

Development Configuration
=========================

For development environments, you can override default settings:

Debug Mode
----------

.. code-block:: bash

   # Enable debug mode
   DEBUG=true
   LOG_LEVEL=DEBUG
   
   # Enable detailed logging
   LANGCHAIN_VERBOSE=true
   LANGCHAIN_DEBUG=true

Testing Configuration
---------------------

.. code-block:: bash

   # Use test database/services
   TESTING=true
   MCP_BASE_URL=http://localhost:3006/api/mcp  # Test MCP server
   
   # Disable external services for unit tests
   DISABLE_LANGSMITH=true
   LLM_PROVIDER=mock

Production Configuration
========================

For production deployments:

Security Settings
-----------------

.. code-block:: bash

   # Security settings
   SECRET_KEY=your-secret-key-here
   ALLOWED_HOSTS=your-domain.com,api.your-domain.com
   
   # HTTPS settings
   FORCE_HTTPS=true
   SECURE_COOKIES=true

Performance Settings
--------------------

.. code-block:: bash

   # Performance tuning
   WORKERS=4
   MAX_REQUESTS=1000
   MAX_REQUESTS_JITTER=100
   
   # Memory optimization
   MEMORY_MAX_TOKENS=1000
   MEMORY_RETURN_MESSAGES=10

Monitoring
----------

.. code-block:: bash

   # Monitoring and observability
   ENABLE_METRICS=true
   METRICS_PORT=9090
   
   # Health check settings
   HEALTH_CHECK_INTERVAL=30

Docker Configuration
====================

When using Docker, you can configure Pili through:

Docker Compose
--------------

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   services:
     pili:
       build: .
       environment:
         - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
         - OPENAI_API_KEY=${OPENAI_API_KEY}
         - MCP_BASE_URL=http://mcp-server:3005/api/mcp
       ports:
         - "8000:8000"

Environment File
----------------

.. code-block:: bash

   # .env for Docker
   COMPOSE_PROJECT_NAME=pili-chatbot
   PILI_IMAGE=pili:latest
   PILI_PORT=8000

Configuration Validation
=========================

Pili validates configuration on startup. Check the logs for configuration errors:

.. code-block:: bash

   # Start with verbose logging to see configuration
   LOG_LEVEL=DEBUG uvicorn main:app --reload

Common validation errors:

* **Missing API keys**: Ensure all required API keys are set
* **Invalid URLs**: Check MCP server URL format and accessibility  
* **Memory settings**: Verify memory limits are within reasonable bounds

Configuration Templates
========================

Sample configurations for different environments:

Development Template
--------------------

.. code-block:: bash

   # .env.development
   LANGCHAIN_API_KEY=your-key
   OPENAI_API_KEY=your-key
   LLM_PROVIDER=openai
   MCP_BASE_URL=http://localhost:3005/api/mcp
   LOG_LEVEL=DEBUG
   DEBUG=true

Production Template
-------------------

.. code-block:: bash

   # .env.production
   LANGCHAIN_API_KEY=your-production-key
   OPENAI_API_KEY=your-production-key
   LLM_PROVIDER=openai
   MCP_BASE_URL=https://api.scaffoldyourshape.com/mcp
   LOG_LEVEL=INFO
   FORCE_HTTPS=true
   WORKERS=4

Testing Template
----------------

.. code-block:: bash

   # .env.test
   TESTING=true
   LLM_PROVIDER=mock
   MCP_BASE_URL=http://localhost:3006/api/mcp
   LOG_LEVEL=WARNING
   DISABLE_LANGSMITH=true

.. tip::
   Always use different API keys and endpoints for development, testing, and production environments.

.. warning::
   Never commit real API keys to version control. Use environment-specific ``.env`` files and add them to ``.gitignore``. 