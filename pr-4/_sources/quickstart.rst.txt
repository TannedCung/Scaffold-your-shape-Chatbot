Quick Start Guide
=================

This guide will get you up and running with Pili in just a few minutes!

🚀 5-Minute Setup
=================

Assuming you have already completed the :doc:`installation`, let's get Pili chatting:

1. **Start the Server**

   .. code-block:: bash

      conda activate Pili
      uvicorn main:app --reload

   You should see output like:

   .. code-block:: text

      INFO:     Will watch for changes in these directories: ['/path/to/project']
      INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
      INFO:     Started reloader process [12345] using StatReload

2. **Test the API**

   Open your browser and go to http://localhost:8000/api/docs to see the interactive API documentation.

3. **Send Your First Message**

   .. code-block:: bash

      curl -X POST "http://localhost:8000/api/chat" \
           -H "Content-Type: application/json" \
           -d '{
             "user_id": "quickstart_user",
             "message": "Hello Pili!"
           }'

   You should get a response like:

   .. code-block:: json

      {
        "response": "Hello! I'm Pili, your fitness companion! 🏃‍♀️ How can I help you today?",
        "logs": []
      }

🎯 First Interactions
=====================

Let's try some basic interactions to understand what Pili can do:

**Log a Workout**

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/chat" \
        -H "Content-Type: application/json" \
        -d '{
          "user_id": "quickstart_user",
          "message": "I ran 5 kilometers this morning in 30 minutes"
        }'

**Ask for Motivation**

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/chat" \
        -H "Content-Type: application/json" \
        -d '{
          "user_id": "quickstart_user",
          "message": "I need some motivation to keep exercising"
        }'

**Request a Workout Plan**

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/chat" \
        -H "Content-Type: application/json" \
        -d '{
          "user_id": "quickstart_user",
          "message": "Can you create a beginner running plan for me?"
        }'

📱 Using the Interactive API
============================

The easiest way to test Pili is through the interactive API documentation:

1. **Open Swagger UI**: http://localhost:8000/api/docs
2. **Click on POST /api/chat**
3. **Click "Try it out"**
4. **Enter your test data**:

   .. code-block:: json

      {
        "user_id": "test_user_123",
        "message": "Show me my workout progress this week"
      }

5. **Click "Execute"**

🧠 Understanding Pili's Responses
=================================

Pili's responses include several components:

.. code-block:: json

   {
     "response": "Main response text from Pili",
     "logs": [
       {
         "agent": "orchestration",
         "action": "route_request",
         "details": "Routed to Logger Agent for activity logging"
       }
     ]
   }

**Response Components:**

* ``response``: The main message from Pili to the user
* ``logs``: Debug information showing which agents were involved

🔧 Configuration Check
======================

Let's verify your configuration is working:

**Health Check**

.. code-block:: bash

   curl http://localhost:8000/api/health

**Memory Status**

.. code-block:: bash

   curl http://localhost:8000/api/memory/stats/quickstart_user

**Available Endpoints**

Visit http://localhost:8000/api/docs to see all available endpoints.

🎭 Agent System Demo
====================

Pili uses a 3-agent orchestration system. Here's how to see it in action:

**Simple Logging (Uses Logger Agent)**

.. code-block:: json

   {
     "user_id": "demo_user",
     "message": "I did 50 push-ups today"
   }

**Complex Planning (Uses Logger + Coach Agents)**

.. code-block:: json

   {
     "user_id": "demo_user",
     "message": "Analyze my running progress and suggest improvements"
   }

**Motivational Support (Uses Coach Agent)**

.. code-block:: json

   {
     "user_id": "demo_user",
     "message": "I'm feeling unmotivated. Help me get back on track."
   }

Watch the ``logs`` field in responses to see which agents are activated!

🔌 MCP Server Integration
=========================

If you have the Scaffold Your Shape MCP server running, test the integration:

.. code-block:: bash

   # Test MCP connectivity
   curl -X POST "http://localhost:8000/api/chat" \
        -H "Content-Type: application/json" \
        -d '{
          "user_id": "mcp_test_user",
          "message": "Show me available fitness clubs"
        }'

.. note::
   The MCP server should be running at ``http://192.168.1.98:3005`` (configurable via ``MCP_BASE_URL``).

🚨 Common Issues & Solutions
============================

**Server Won't Start**

.. code-block:: bash

   # Check if port 8000 is in use
   lsof -i :8000
   
   # Use a different port
   uvicorn main:app --reload --port 8001

**Memory Errors**

.. code-block:: bash

   # Clear user memory if needed
   curl -X POST "http://localhost:8000/api/memory/clear" \
        -H "Content-Type: application/json" \
        -d '{"user_id": "your_user_id"}'

**API Key Issues**

Check your ``.env`` file has valid keys:

.. code-block:: bash

   cat .env | grep -E "(OPENAI_API_KEY|LANGCHAIN_API_KEY)"

🎉 Next Steps
=============

Now that Pili is running:

1. **Learn about Architecture**: :doc:`architecture/overview`
2. **Explore Configuration**: :doc:`configuration`
3. **Try More Examples**: :doc:`examples/basic_usage`

💡 Pro Tips
===========

* **Use descriptive user_ids**: This helps with debugging and memory management
* **Check the logs**: The ``logs`` field shows you what's happening under the hood
* **Try conversational flow**: Send multiple messages with the same ``user_id`` to test memory
* **Monitor with LangSmith**: If configured, check your LangSmith dashboard for detailed traces

.. tip::
   For production use, make sure to review the configuration guide carefully!

Happy chatting with Pili! 🏃‍♀️💪 