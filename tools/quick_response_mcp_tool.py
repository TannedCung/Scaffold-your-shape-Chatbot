"""Quick Response MCP Tool for Pili's Orchestrator Agent.

This tool provides immediate responses for casual queries, comments, and common questions
without needing to route to specialized agents or external services.
"""

import json
import random
from datetime import datetime
from typing import Dict, Any, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class QuickResponseInput(BaseModel):
    """Input schema for the quick response tool."""
    
    query_type: str = Field(
        description="Type of query: 'greeting', 'casual', 'motivation', 'general_fitness', 'comment', 'thanks'"
    )
    user_query: str = Field(description="The original user query or comment")
    user_id: str = Field(description="User ID for personalization")
    context: Optional[str] = Field(default="", description="Additional context if available")


class QuickResponseTool(BaseTool):
    """Tool for generating quick responses to casual queries and comments."""
    
    name: str = "quick_response"
    description: str = """
    Generate immediate, friendly responses for casual queries, greetings, comments, and general fitness questions.
    Use this tool for:
    - Greetings: "Hi", "Hello", "Good morning"
    - Thanks: "Thank you", "Thanks"
    - Casual comments: "That's great", "Awesome", "Cool"
    - General fitness questions: "How to stay motivated?", "Best time to exercise?"
    - Motivational requests: "I need motivation", "Encourage me"
    - Simple comments that don't require data or specialized agent routing
    
    Do NOT use for:
    - Activity logging (use Logger Agent)
    - Progress tracking (use Logger Agent) 
    - Workout planning (use Coach Agent)
    - Complex fitness analysis (use Coach Agent)
    """
    args_schema: Type[BaseModel] = QuickResponseInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _load_response_templates(self) -> Dict[str, list]:
        """Load response templates for different query types."""
        return {
            "greeting": [
                "Hey there! 👋 I'm Pili, your fitness companion! Ready to crush some goals today? 💪",
                "Hello! 🌟 Great to see you! What fitness adventure are we going on today? 🏃‍♀️",
                "Hi! 👋 Welcome to your fitness journey with Pili! How can I help you stay awesome today? ✨",
                "Hey! 🔥 Ready to make today amazing? I'm here to support your fitness goals! 💪",
                "Hello there! 🌈 Pili here, and I'm excited to help you on your fitness journey! What's up? 🚀"
            ],
            "thanks": [
                "You're so welcome! 😊 I'm always here to support your fitness journey! Keep being awesome! 💪",
                "My pleasure! 🌟 Helping you reach your goals is what I live for! You've got this! 🔥",
                "Anytime! 👍 Your dedication to fitness is inspiring! Keep up the great work! 🏆",
                "You're welcome! 😄 Remember, I'm always here whenever you need fitness support! 💚",
                "Happy to help! ✨ Your commitment to health and fitness is amazing! Stay strong! 💪"
            ],
            "casual": [
                "Absolutely! 🎉 Your positive energy is contagious! Keep that momentum going! 💫",
                "I love your enthusiasm! 🔥 That attitude will take you far in your fitness journey! 🚀",
                "Yes! 🙌 Your excitement motivates me too! Let's keep this energy high! ⚡",
                "That's the spirit! 💪 Your positivity is exactly what successful fitness journeys are made of! 🌟",
                "Right on! 🎯 I can feel your determination through the screen! You're unstoppable! 🏆"
            ],
            "motivation": [
                "You've got this! 💪 Remember, every small step counts and you're stronger than you think! 🔥",
                "Believe in yourself! 🌟 Your body can achieve amazing things when your mind is determined! 💯",
                "You're unstoppable! 🚀 Every workout, every healthy choice, every step forward matters! 🏆", 
                "Stay strong! 💪 Progress isn't always visible, but it's always happening when you don't give up! ⚡",
                "You're amazing! 🌈 Your commitment to your health is inspiring and you're making it happen! 🔥",
                "Keep pushing! 💥 Great things never come from comfort zones - you're exactly where you need to be! 🎯"
            ],
            "general_fitness": [
                "Great question! 🤔 Consistency is key in fitness - small daily actions create big results over time! 💪",
                "Love that you're curious! 🧠 The best fitness approach is one you can stick to long-term! 🎯",
                "Excellent thinking! 💡 Listen to your body, stay consistent, and celebrate small wins! 🏆",
                "Smart question! 🤓 Focus on progress, not perfection - every step forward counts! 🌟",
                "That's the right mindset! 🔥 The best workout is the one you'll actually do consistently! ⚡"
            ],
            "comment": [
                "I appreciate your feedback! 🙏 Your fitness journey is unique and I'm here to support you! 💚",
                "Thanks for sharing! 💭 Every comment helps me understand how to better support your goals! 🌟",
                "Your input matters! 📝 I'm always learning how to be a better fitness companion! 💪",
                "Great point! 🎯 Your perspective helps me provide better fitness support for everyone! 🤝",
                "Thanks for that! 💬 I value your thoughts on your fitness journey! Keep them coming! ✨"
            ]
        }
    
    def _get_time_appropriate_greeting(self) -> str:
        """Get time-appropriate greeting addition."""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return "Good morning! ☀️ "
        elif 12 <= current_hour < 17:
            return "Good afternoon! 🌤️ "
        elif 17 <= current_hour < 21:
            return "Good evening! 🌅 "
        else:
            return "Hope you're having a great day! 🌙 "
    
    def _personalize_response(self, response: str, user_id: str, context: str = "") -> str:
        """Add personalization to the response."""
        # Add time-appropriate greeting for greetings
        if any(word in response.lower() for word in ["hello", "hi", "hey"]):
            response = self._get_time_appropriate_greeting() + response
        
        # Add context if provided
        if context and "progress" in context.lower():
            response += " I see you're making great progress! 📈"
        elif context and "goal" in context.lower():
            response += " Your goals are within reach! 🎯"
        
        return response
    
    def _run(self, query_type: str, user_query: str, user_id: str, context: str = "") -> str:
        """Generate a quick response based on the query type."""
        try:
            # Normalize query type
            query_type = query_type.lower().strip()
            
            # Get response templates
            response_templates = self._load_response_templates()
            
            # Default to casual if type not recognized
            if query_type not in response_templates:
                query_type = "casual"
            
            # Get random response from templates
            responses = response_templates[query_type]
            base_response = random.choice(responses)
            
            # Personalize the response
            personalized_response = self._personalize_response(base_response, user_id, context)
            
            # Add some variety based on query content
            query_lower = user_query.lower()
            
            # Special handling for specific phrases
            if "tired" in query_lower or "exhausted" in query_lower:
                personalized_response += " Rest is just as important as training! 😴"
            elif "excited" in query_lower or "pumped" in query_lower:
                personalized_response += " That energy is going to fuel amazing workouts! ⚡"
            elif "nervous" in query_lower or "worried" in query_lower:
                personalized_response += " It's normal to feel that way - you're about to do something great! 🌟"
            
            return personalized_response
            
        except Exception as e:
            # Fallback response
            return f"Thanks for reaching out! 😊 I'm here to support your fitness journey! How can I help you today? 💪"
    
    async def _arun(self, query_type: str, user_query: str, user_id: str, context: str = "") -> str:
        """Async version of the run method."""
        return self._run(query_type, user_query, user_id, context)


def create_quick_response_tool() -> QuickResponseTool:
    """Factory function to create the quick response tool."""
    return QuickResponseTool()


# Example usage and testing
if __name__ == "__main__":
    tool = create_quick_response_tool()
    
    # Test different query types
    test_cases = [
        {"query_type": "greeting", "user_query": "Hello!", "user_id": "test_user"},
        {"query_type": "thanks", "user_query": "Thank you so much!", "user_id": "test_user"},
        {"query_type": "motivation", "user_query": "I need some motivation", "user_id": "test_user"},
        {"query_type": "casual", "user_query": "That's awesome!", "user_id": "test_user"},
        {"query_type": "general_fitness", "user_query": "What's the best time to exercise?", "user_id": "test_user"},
    ]
    
    print("Testing Quick Response Tool:")
    print("=" * 50)
    
    for test in test_cases:
        response = tool._run(**test)
        print(f"Query: {test['user_query']}")
        print(f"Type: {test['query_type']}")
        print(f"Response: {response}")
        print("-" * 30)
