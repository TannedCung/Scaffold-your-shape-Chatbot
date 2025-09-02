Basic Usage Examples
====================

Getting Started
===============

Start Pili:

.. code-block:: bash

   conda activate Pili
   uvicorn main:app --reload

Basic Examples
==============

**Simple Greeting**

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/chat" \
        -H "Content-Type: application/json" \
        -d '{"user_id": "demo", "message": "Hello Pili!"}'

**Log Activity**

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/chat" \
        -H "Content-Type: application/json" \
        -d '{"user_id": "demo", "message": "I ran 5km in 30 minutes"}'

**Request Plan**

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/chat" \
        -H "Content-Type: application/json" \
        -d '{"user_id": "demo", "message": "Create a beginner running plan"}'

**Get Motivation**

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/chat" \
        -H "Content-Type: application/json" \
        -d '{"user_id": "demo", "message": "I need motivation to exercise"}'

API Endpoints
=============

- ``POST /api/chat`` - Main chat interface
- ``GET /api/health`` - Health check
- ``GET /api/memory/stats/{user_id}`` - Memory statistics
- ``POST /api/memory/clear`` - Clear user memory
- ``GET /api/docs`` - Interactive API documentation

Next Steps
==========

1. Learn about the :doc:`../architecture/overview` to understand how it works
2. Explore the configuration options in :doc:`../configuration`

.. tip::
   Use descriptive user IDs to help with debugging and conversation management. 