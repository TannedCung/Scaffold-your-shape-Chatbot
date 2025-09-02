Installation Guide
==================

This guide will help you set up Pili, the Exercise Tracker Chatbot, on your system.

Prerequisites
-------------

Before installing Pili, ensure you have the following prerequisites:

* **Python 3.8+**: Download from `python.org <https://www.python.org/downloads/>`_
* **Git**: For cloning the repository
* **Conda** (recommended): For environment management

System Requirements
-------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Component
     - Requirement
   * - **Operating System**
     - Linux, macOS, or Windows 10+
   * - **Python Version**
     - 3.8 or higher
   * - **Memory**
     - Minimum 4GB RAM (8GB recommended)
   * - **Storage**
     - At least 2GB free space
   * - **Network**
     - Internet connection for API calls

Quick Installation
------------------

1. **Clone the Repository**

   .. code-block:: bash

      git clone <repository-url>
      cd Scaffold-your-shape-Chatbot

2. **Create Conda Environment**

   .. code-block:: bash

      conda create -n Pili python=3.11
      conda activate Pili

3. **Install Dependencies**

   .. code-block:: bash

      pip install -r requirements.txt

4. **Configure Environment**

   .. code-block:: bash

      cp .env.sample .env
      # Edit .env with your actual configuration values

5. **Run the Application**

   .. code-block:: bash

      uvicorn main:app --reload

6. **Verify Installation**

   Open your browser and navigate to:

   * **API Documentation**: http://localhost:8000/api/docs
   * **Health Check**: http://localhost:8000/api/health

Environment Configuration
--------------------------

Create a ``.env`` file in the project root with the following variables:

.. code-block:: bash

   # LangChain Configuration
   LANGCHAIN_API_KEY=your_langchain_api_key_here
   LANGCHAIN_PROJECT=pili-exercise-chatbot

   # LLM Provider Configuration
   LLM_PROVIDER=openai  # Options: openai, ollama, vllm, local
   OPENAI_API_KEY=your_openai_api_key_here

   # Local LLM Configuration (if using local provider)
   LOCAL_LLM_BASE_URL=http://localhost:11434
   LOCAL_LLM_MODEL=llama2

   # MCP Server Configuration
   MCP_BASE_URL=http://192.168.1.98:3005/api/mcp

Docker Installation
-------------------

For a containerized deployment:

1. **Using Docker Compose**

   .. code-block:: bash

      docker-compose up -d

2. **With VLLM Support**

   .. code-block:: bash

      docker-compose -f docker-compose.yml -f docker-compose.vllm.yml up -d

3. **Production Deployment**

   .. code-block:: bash

      docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

Development Setup
-----------------

For development work, follow these additional steps:

1. **Install Development Dependencies**

   .. code-block:: bash

      pip install -r requirements.txt
      pip install pytest pytest-asyncio black isort mypy

2. **Pre-commit Hooks** (Optional)

   .. code-block:: bash

      pip install pre-commit
      pre-commit install

3. **Run Tests**

   .. code-block:: bash

      pytest

Troubleshooting
---------------

Common installation issues and solutions:

**Port Already in Use**

.. code-block:: bash

   # Find process using port 8000
   lsof -i :8000
   
   # Kill the process or use a different port
   uvicorn main:app --reload --port 8001

**Permission Errors**

.. code-block:: bash

   # On Linux/macOS, you may need to use sudo for global installs
   # It's recommended to use virtual environments instead

**Dependency Conflicts**

.. code-block:: bash

   # Create a fresh environment
   conda deactivate
   conda remove -n Pili --all
   conda create -n Pili python=3.11
   conda activate Pili
   pip install -r requirements.txt

**Memory Issues**

If you encounter memory issues:

* Ensure you have at least 4GB RAM available
* Close other applications
* Consider using a smaller LLM model for local deployments

Next Steps
----------

After successful installation:

1. Read the :doc:`quickstart` guide
2. Configure your :doc:`configuration` settings
3. Explore the :doc:`architecture/overview`
4. Try the :doc:`examples/basic_usage`

.. tip::
   For production deployments, review the configuration guide carefully.

.. warning::
   Make sure to never commit your ``.env`` file with real API keys to version control! 