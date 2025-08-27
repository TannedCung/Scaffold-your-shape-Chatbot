"""Quick Response Tool for immediate responses.

This tool provides immediate responses for casual queries and automatically 
terminates the conversation flow through the custom react agent.
"""

from typing import Optional
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
import random


def create_quick_response_command_tool():
    """Create a quick response tool that terminates conversation flow."""
    
    @tool("quick_response", description="""
    Provides immediate, casual responses for common queries like greetings, thanks, simple comments,
    general fitness questions, or motivation requests. This tool routes directly to END after responding,
    terminating the conversation flow (similar to how transfer tools route to other agents).
    
    Use this tool for:
    - Greetings (Hi, Hello, Hey)
    - Thanks/appreciation (Thank you, Thanks)
    - Simple comments (Great, Cool, Nice)
    - General fitness questions (How to build muscle?, What's a good workout?)
    - Motivation requests (Need motivation, Encourage me)
    - Casual interactions that don't require specialized agent processing
    
    Parameters:
    - query_type: Type of query (greeting, thanks, casual, general_fitness, motivation, comment)
    - user_query: The original user message
    - user_id: The ID of the user making the request
    - context: Any relevant conversation context (optional)
    """)
    def quick_response(
        query_type: str,
        user_query: str, 
        user_id: str,
        context: Optional[str] = None,
        state: Annotated[dict, InjectedState] = None,
        tool_call_id: Annotated[str, InjectedToolCallId] = None,
    ):
        """Generate quick response and route to END."""
        
        # Response templates for different query types
        response_templates = {
            "greeting": [
                "Hello! 👋 Ready to help you achieve your fitness goals!",
                "Hi there! 💪 What fitness challenge can I help you tackle today?",
                "Hey! 🌟 I'm here to support your health and wellness journey!",
                "Hello! 🏃‍♀️ Let's make today a great day for your fitness!",
                "Hi! ✨ Ready to crush some fitness goals together?"
            ],
            "thanks": [
                "You're very welcome! 😊 Happy to help on your fitness journey!",
                "My pleasure! 💪 Keep up the great work!",
                "Anytime! 🌟 I'm here whenever you need fitness support!",
                "You're welcome! 🏆 Proud of your dedication to health!",
                "Glad I could help! 💫 Keep pushing toward your goals!"
            ],
            "casual": [
                "Great to hear from you! 😊 How can I support your fitness today?",
                "Nice! 💪 What's on your fitness agenda?",
                "Awesome! 🌟 Ready to help you stay on track!",
                "Cool! 🏃‍♀️ Let's keep that momentum going!",
                "Sweet! ✨ What fitness goals are we working on?"
            ],
            "general_fitness": [
                "Great question! 💪 For personalized fitness advice, I'd recommend checking with a fitness professional. In general, consistency and proper form are key!",
                "That's a fantastic fitness question! 🏋️‍♀️ While I can offer general encouragement, a certified trainer would give you the best specific guidance!",
                "Love your curiosity about fitness! 🌟 For detailed workout plans, consider consulting with fitness experts who can tailor advice to your needs!",
                "Excellent fitness mindset! 💫 General principle: start with basics, progress gradually, and listen to your body. Professional guidance is always best!",
                "Great fitness focus! 🏆 Remember: proper nutrition, adequate rest, and consistent exercise are the foundation. Seek professional advice for specifics!"
            ],
            "motivation": [
                "You've got this! 💪 Every step forward, no matter how small, is progress!",
                "Keep going! 🌟 Your commitment to fitness is inspiring!",
                "You're stronger than you think! 🏆 Trust the process and stay consistent!",
                "Believe in yourself! ✨ Every workout makes you stronger physically and mentally!",
                "You're on the right path! 🚀 Progress takes time, but you're worth the effort!"
            ],
            "comment": [
                "Thanks for sharing! 😊 How else can I support your fitness journey?",
                "Appreciate your input! 💪 What fitness goals are you working on?",
                "Great to hear! 🌟 Anything specific I can help you with today?",
                "Nice! 🏃‍♀️ How can I help you stay motivated and on track?",
                "Awesome! ✨ What's next on your wellness journey?"
            ]
        }
        
        # Get response template
        templates = response_templates.get(query_type, response_templates["casual"])
        response = random.choice(templates)
        
        # Personalize response if user_id is meaningful
        if user_id and user_id != "test_user" and len(user_id) > 5:
            response = f"{response} Great to see you again!"
        
        # Add context if provided
        if context and len(context.strip()) > 0:
            response += f" (Context noted: {context[:50]}...)"
        
        # Handle case where tool_call_id might be None (e.g., in testing or direct calls)
        actual_tool_call_id = tool_call_id if tool_call_id is not None else f"quick_response_{hash(response) % 10000}"
        
        # Create tool message for the response
        tool_message = ToolMessage(
            content=response,
            name="quick_response",
            tool_call_id=actual_tool_call_id,
        )
        
        # For langgraph_swarm, we just return the tool message
        # The custom react agent will handle the termination logic
        return tool_message

        # # Return Command that routes to END (like handoff tools route to agents)
        # return Command(
        #     goto="__end__",  # Special LangGraph END node
        #     update={"messages": state["messages"] + [tool_message]}
        # )
    
    return quick_response


# Create a convenience function for backward compatibility
def create_quick_response_tool():
    """Create quick response tool - now uses Command routing."""
    return create_quick_response_command_tool()


