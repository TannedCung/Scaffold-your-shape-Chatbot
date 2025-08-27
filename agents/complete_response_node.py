"""Complete Response Node for the LangGraph workflow.

This module provides the complete response node that replaces the completion response tool.
It's executed as a node in the graph after logger and coach agents complete their work.
"""

from typing import Dict, Any, Optional
from langchain_core.messages import AIMessage, ToolMessage
from agents.agent import get_model
from langgraph.prebuilt import create_react_agent


def create_complete_response_node():
    """Create a complete response agent that behaves like other agents in langgraph_swarm."""
    
    # Create a simple prompt for the complete response agent
    complete_response_prompt = """You are Pili's completion response generator. 

When you receive a request, create a warm, encouraging completion response that:
1. Acknowledges what was accomplished by previous agents
2. Provides encouragement using fitness emojis
3. Offers support for future fitness goals
4. Keeps it concise (2-3 sentences max)

Look at the conversation history to understand what was accomplished and create an appropriate final response."""
    
    # Create a react agent with no tools for the complete response
    complete_response_agent = create_react_agent(
        get_model(),
        tools=[],  # No tools needed for final response
        prompt=complete_response_prompt,
        name="complete_response_node"
    )
    
    return complete_response_agent
