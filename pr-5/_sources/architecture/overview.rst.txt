Architecture Overview
=====================

Pili implements a sophisticated **3-agent orchestration architecture** designed for scalability, maintainability, and intelligent request handling.

System Architecture
===================

The Pili architecture consists of multiple layers working together:

.. mermaid::

   graph TB
       %% Main API Layer
       API["REST API Layer<br/>FastAPI + Swagger UI"]
       
       %% Orchestration Agent
       ORCH["🎯 Orchestration Agent<br/>Request Router & Coordinator"]
       
       %% Specialized Agents
       LOGGER["📝 Logger Agent<br/>MCP Integration"]
       COACH["🏃‍♀️ Coach Agent<br/>AI Planning"]
       
       %% External Services
       MCP["MCP Server<br/>Scaffold Shape"]
       MEMORY["Memory Service<br/>Conversation History"]
       LLM["LLM Provider<br/>OpenAI/Local/VLLM"]
       
       %% Connections
       API --> ORCH
       ORCH --> LOGGER
       ORCH --> COACH
       LOGGER --> MCP
       LOGGER --> MEMORY
       COACH --> LLM
       COACH --> MEMORY
       
       %% Styling
       classDef apiLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
       classDef agent fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
       classDef service fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
       
       class API apiLayer
       class ORCH,LOGGER,COACH agent
       class MCP,MEMORY,LLM service

Core Components
===============

1. **Orchestration Agent** 🎯
   - Entry point for all user requests
   - Intelligent routing based on intent analysis
   - Response coordination and formatting
   - Conversation flow management

2. **Logger Agent** 📝
   - Direct integration with MCP server
   - Activity tracking and logging
   - Club management operations
   - Data retrieval and synchronization

3. **Coach Agent** 🏃‍♀️
   - AI-powered workout planning
   - Progress analysis and insights
   - Motivational coaching
   - Personalized recommendations

4. **Memory Service** 🧠
   - Persistent conversation history
   - User context maintenance
   - Session management
   - Cross-agent data sharing

Agent Interaction Patterns
===========================

Simple Request Flow
-------------------

For straightforward requests (e.g., "Log my run"):

.. code-block:: text

   1. User sends message to REST API
   2. Orchestration Agent analyzes intent
   3. Routes to Logger Agent
   4. Logger Agent calls MCP server
   5. Response flows back through Orchestration Agent
   6. Formatted response returned to user

Complex Request Flow
--------------------

For multi-step requests (e.g., "Analyze my progress and suggest improvements"):

.. code-block:: text

   1. User sends message to REST API
   2. Orchestration Agent identifies complex intent
   3. Coordinates Logger Agent (data retrieval)
   4. Coordinates Coach Agent (analysis & planning)
   5. Orchestration Agent combines results
   6. Formatted comprehensive response returned

Request Routing Logic
=====================

The Orchestration Agent uses sophisticated intent analysis:

**Intent Categories**

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * - Intent Type
     - Keywords/Patterns
     - Target Agent
     - Examples
   * - **Activity Logging**
     - "ran", "did", "completed", "workout"
     - Logger Agent
     - "I ran 5k today"
   * - **Data Retrieval**
     - "show", "get", "history", "progress"
     - Logger Agent
     - "Show my activities"
   * - **Planning**
     - "plan", "schedule", "program", "routine"
     - Coach Agent
     - "Create a training plan"
   * - **Analysis**
     - "analyze", "insights", "trends", "compare"
     - Logger + Coach
     - "Analyze my progress"
   * - **Motivation**
     - "motivation", "encourage", "support"
     - Coach Agent
     - "I need motivation"

**Decision Tree**

.. code-block:: python

   def analyze_intent(user_message: str) -> AgentRoute:
       if contains_activity_data(user_message):
           return Route.LOGGER_AGENT
       elif contains_planning_request(user_message):
           return Route.COACH_AGENT
       elif contains_analysis_request(user_message):
           return Route.LOGGER_AND_COACH
       elif contains_motivation_request(user_message):
           return Route.COACH_AGENT
       else:
           return Route.ORCHESTRATION_ONLY

Technology Stack
================

**Core Framework**
- **FastAPI**: High-performance REST API framework
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

**AI/ML Stack**
- **LangChain**: Agent orchestration and LLM integration
- **LangGraph**: Multi-agent workflow management
- **LangSmith**: Monitoring and observability

**LLM Integration**
- **OpenAI**: Primary LLM provider
- **Local LLMs**: Ollama, VLLM support
- **Streaming**: Real-time response generation

**External Integration**
- **MCP Protocol**: Scaffold Your Shape integration
- **HTTP/REST**: External service communication

Data Flow Architecture
======================

**Memory Management**

.. code-block:: text

   User Request → Memory Retrieval → Agent Processing → Memory Update → Response

**Conversation Context**
- Each user has isolated conversation history
- Agents share context through memory service
- Session-based memory management
- Automatic memory cleanup and optimization

**Error Handling**
- Graceful degradation on external service failures
- Retry logic with exponential backoff
- Fallback responses when agents are unavailable
- Comprehensive error logging and monitoring

Scalability Considerations
==========================

**Horizontal Scaling**
- Stateless agent design
- External memory service
- Load balancer compatible
- Container-ready architecture

**Performance Optimization**
- Async/await throughout
- Connection pooling
- Response caching where appropriate
- Memory usage optimization

**Monitoring & Observability**
- LangSmith integration for AI monitoring
- Structured logging
- Health check endpoints
- Metrics collection

Security Architecture
=====================

**API Security**
- Input validation and sanitization
- Rate limiting
- CORS configuration
- Environment-based secrets management

**External Service Security**
- Secure API key management
- TLS/HTTPS enforcement
- Request/response validation
- Timeout and retry limits

**Data Privacy**
- User data isolation
- Memory encryption options
- Audit logging
- GDPR compliance ready

Deployment Architecture
=======================

**Container Strategy**
- Docker containerization
- Docker Compose for development
- Production-ready Dockerfile
- Health check integration

**Environment Management**
- Development/staging/production configs
- Environment variable management
- Secrets management
- Configuration validation

**Monitoring & Logging**
- Centralized logging
- Application metrics
- Health monitoring
- Error tracking

Future Architecture Considerations
==================================

**Agent Extensibility**
- Plugin architecture for new agents
- Dynamic agent registration
- Agent-specific configuration
- Hot-reloading capabilities

**Advanced Features**
- Multi-language support
- Voice interface integration
- Real-time notifications
- Advanced analytics

**Integration Expansion**
- Additional fitness platform support
- Third-party service integrations
- Webhook support
- GraphQL API option

This architecture provides a solid foundation for Pili's current capabilities while maintaining flexibility for future enhancements and scaling requirements. 