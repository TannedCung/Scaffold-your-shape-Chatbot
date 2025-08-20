Welcome to Pili's Documentation!
==================================

.. image:: https://img.shields.io/badge/Python-3.8+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/FastAPI-0.116+-green.svg
   :target: https://fastapi.tiangolo.com/
   :alt: FastAPI Version

.. image:: https://img.shields.io/badge/LangChain-0.3+-orange.svg
   :target: https://python.langchain.com/
   :alt: LangChain Version

**Pili** is a sophisticated multiagent chatbot microservice for exercise tracking, built with FastAPI, LangGraph, and LangSmith. 
It features a **3-agent orchestration architecture** with **intelligent routing** and **MCP server integration** for the Scaffold Your Shape fitness platform.

🏗️ Architecture Overview
========================

Pili implements a cutting-edge 3-agent orchestration system:

* **🎯 Orchestration Agent**: Intelligent request routing and response coordination
* **📝 Logger Agent**: Direct MCP server integration for activity tracking
* **🏃‍♀️ Coach Agent**: AI-powered workout planning and progress analysis

🚀 Key Features
===============

* **Intelligent Request Routing**: Advanced NLP-based intent detection
* **Real-time Streaming**: FastAPI streaming responses with orchestration metadata
* **Conversation Memory**: Persistent context across user interactions
* **MCP Server Integration**: Direct connection to Scaffold Your Shape platform
* **Robust Error Handling**: Graceful fallbacks for all components
* **Auto-generated API Documentation**: Interactive Swagger UI

📚 Documentation Structure
==========================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart
   configuration

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture/overview

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/basic_usage

🤖 What Can Pili Do?
====================

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Category
     - Example Messages
     - Agent Flow
   * - **Activity Logging**
     - "I ran 5 km", "Did yoga for 45 minutes"
     - Orchestration → Logger → MCP Server
   * - **Club Management**
     - "Show me clubs", "Join club runners"
     - Orchestration → Logger → MCP Server
   * - **Workout Planning**
     - "Create a running plan", "I need a training schedule"
     - Orchestration → Logger (data) + Coach (planning)
   * - **Progress Analysis**
     - "How am I doing?", "Analyze my progress"
     - Orchestration → Logger (data) + Coach (analysis)
   * - **Motivation**
     - "I need motivation", "Encourage me"
     - Orchestration → Coach with context

🔗 Quick Links
==============

* **GitHub Repository**: `Scaffold-your-shape-Chatbot <https://github.com/your-org/Scaffold-your-shape-Chatbot>`_
* **API Documentation**: http://localhost:8000/api/docs
* **LangSmith Dashboard**: `Monitor Conversations <https://smith.langchain.com/>`_
* **Scaffold Your Shape**: `Main Platform <http://192.168.1.98:3005>`_

📧 Support
==========

If you encounter any issues or have questions:

* Check the installation guide
* Review the quickstart section
* Open an issue on GitHub
* Contact the development team

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

---

**Meet Pili** - Your friendly AI fitness companion that makes tracking workouts as easy as having a conversation! 🏃‍♀️💪 