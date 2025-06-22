import json
import time
from typing import Dict, Any, Optional, Generator
from openai import OpenAI
import httpx
from config.settings import settings

class LLMService:
    """Service for LLM-based intent detection and response generation with multiple provider support."""
    
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.setup_client()
    
    def setup_client(self):
        """Setup the appropriate LLM client based on provider."""
        if self.provider == "openai":
            self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
            self.model = settings.openai_model
        elif self.provider in ["ollama", "vllm", "local"]:
            # For local providers, use OpenAI-compatible client with custom base_url
            api_key = settings.local_llm_api_key or "not-required"
            self.client = OpenAI(
                base_url=settings.local_llm_base_url,
                api_key=api_key
            )
            self.model = settings.local_llm_model
        else:
            print(f"Unknown LLM provider: {self.provider}")
            self.client = None
            self.model = "unknown"
    
    def detect_intent(self, user_message: str, conversation_history: list = None) -> Dict[str, Any]:
        """Detect intent from user message using LLM."""
        if not self.client:
            # Fallback to rule-based detection if no LLM available
            return self._fallback_intent_detection(user_message)
        
        system_prompt = """You are Pili, a fitness chatbot. Analyze the user's message and determine their intent.

Available intents:
- log_activity: User wants to record a fitness activity (running, cycling, swimming, etc.)
- manage_clubs: User wants to create, join, or find fitness clubs
- manage_challenges: User wants to create, join, or view fitness challenges
- get_stats: User wants to see their fitness progress/statistics
- help: User needs help or wants to know what you can do
- unknown: Message doesn't fit other categories

Consider the conversation history for context clues and references to previous messages.

Respond in JSON format:
{
    "intent": "one_of_the_above",
    "confidence": 0.8,
    "extracted_info": {
        "activity_type": "running/cycling/etc (if applicable)",
        "distance": "5 km (if mentioned)",
        "duration": "30 minutes (if mentioned)",
        "location": "park (if mentioned)"
    }
}"""

        try:
            # Build messages including conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if available (limit to last 10 messages to avoid token limits)
            if conversation_history:
                recent_history = conversation_history[-10:]  # Keep last 10 messages
                for msg in recent_history:
                    if hasattr(msg, 'type'):
                        # Convert langchain message format
                        role = "user" if msg.type == "human" else "assistant"
                        messages.append({"role": role, "content": msg.content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Adjust parameters based on provider
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 300,
                "extra_body": {
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            }
            
            # For local providers, we might need to adjust parameters
            if self.provider == "ollama":
                # Ollama sometimes needs different parameter names
                params["stream"] = False
            
            # Make synchronous call with timeout handling
            response = self.client.chat.completions.create(**params)
            
            content = response.choices[0].message.content
            
            # Try to parse JSON, handle cases where LLM doesn't return valid JSON
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # Extract intent from text response if JSON parsing fails
                return self._extract_intent_from_text(content, user_message)
            
        except Exception as timeout_e:
            if "timeout" in str(timeout_e).lower():
                print(f"LLM intent detection timed out for message: {user_message}")
                return self._fallback_intent_detection(user_message)
        except Exception as e:
            print(f"LLM intent detection failed: {e}")
            return self._fallback_intent_detection(user_message)
    
    def generate_response(self, intent: str, user_message: str, action_result: str, conversation_history: list = None) -> str:
        """Generate a natural response using LLM."""
        if not self.client:
            return action_result  # Fallback to action result
        
        system_prompt = """You are Pili, an enthusiastic and friendly fitness chatbot. 

Your personality:
- Encouraging and motivational
- Uses fitness emojis appropriately  
- Celebrates user achievements
- Provides helpful fitness advice
- Speaks naturally and conversationally

Based on the conversation history, user's message, intent, and the action result, generate a natural, personalized response.
Keep responses concise but engaging (2-3 sentences max unless it's help/stats content).
Reference previous conversations when relevant to provide continuity.

Based on the provided tools, you can decide to use them or not.

You can use <think> tags to reason through your response, but only the content after </think> will be shown to the user."""

        user_prompt = f"""
User message: "{user_message}"
Intent: {intent}
Action result: {action_result}

Generate a natural, encouraging response as Pili:"""

        try:
            # Build messages including conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if available (limit to last 8 messages to avoid token limits)
            if conversation_history:
                recent_history = conversation_history[-8:]  # Keep last 8 messages for context
                for msg in recent_history:
                    if hasattr(msg, 'type'):
                        # Convert langchain message format
                        role = "user" if msg.type == "human" else "assistant"
                        messages.append({"role": role, "content": msg.content})
            
            # Add current prompt
            messages.append({"role": "user", "content": user_prompt})
            
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 200,
                "extra_body": {
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            }
            
            if self.provider == "ollama":
                params["stream"] = False
            
            response = self.client.chat.completions.create(**params)
            
            content = response.choices[0].message.content.strip()
            
            # Extract content after </think> if present
            content = self._extract_final_response(content)
            
            return content
            
        except Exception as timeout_e:
            if "timeout" in str(timeout_e).lower():
                print(f"LLM response generation timed out for intent: {intent}")
                return action_result  # Fallback to action result
        except Exception as e:
            print(f"LLM response generation failed: {e}")
            return action_result  # Fallback to action result
    
    def generate_response_with_tools(self, context: str, user_message: str, system_prompt: str, conversation_history: list = None, tools: list = None):
        """Generate a response with tool calling capability."""
        if not self.client:
            return {"content": "LLM service unavailable"}

        try:
            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if available
            if conversation_history:
                recent_history = conversation_history[-8:]  # Keep last 8 messages
                for msg in recent_history:
                    if isinstance(msg, dict):
                        messages.append(msg)
                    elif hasattr(msg, 'type'):
                        # Convert langchain message format
                        role = "user" if msg.type == "human" else "assistant"
                        messages.append({"role": role, "content": msg.content})
            
            # Add current user message if not already in conversation history
            if not any(msg.get("content") == user_message for msg in messages if msg.get("role") == "user"):
                messages.append({"role": "user", "content": user_message})
            
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000,
            }
            
            # Add provider-specific parameters for tool calling
            if self.provider in ["ollama", "vllm", "local"]:
                # Some local providers need additional hints for tool calling
                params["extra_body"] = {
                    "chat_template_kwargs": {"enable_thinking": True},
                    "guided_json": None,  # Ensure JSON mode is available for tool calling
                }
            elif self.provider == "openai":
                # OpenAI-specific optimizations
                params["parallel_tool_calls"] = True  # Enable parallel tool execution
            
            # Add tools if provided
            if tools and len(tools) > 0:
                params["tools"] = tools[:1]
                
                # Encourage tool usage - be more aggressive about tool calling
                if len(params["tools"]) == 1:
                    # Force the single tool to be used
                    params["tool_choice"] = {"type": "function", "function": {"name": tools[0]["function"]["name"]}}
                elif len(params["tools"]) <= 3:
                    # For small number of tools, encourage usage but don't force
                    params["tool_choice"] = "required"  # This forces the model to use at least one tool
                else:
                    # For many tools, let model choose but encourage usage
                    params["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**params)
            
            # Debug: Print response details
            message = response.choices[0].message
            return message
            
        except Exception as timeout_e:
            if "timeout" in str(timeout_e).lower():
                print(f"LLM tool response timed out for context: {context}")
                return {"content": "Request timed out"}
        except Exception as e:
            print(f"LLM tool response generation failed: {e}")
            return {"content": f"Error: {str(e)}"}

    def generate_response_stream(self, intent: str, user_message: str, action_result: str, conversation_history: list = None) -> Generator[str, None, None]:
        """Generate a streaming response using LLM."""
        if not self.client:
            # Fallback: yield the action result as chunks
            words = action_result.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield f" {word}"
                time.sleep(0.05)  # Small delay to simulate streaming
            return

        system_prompt = """You are Pili, an enthusiastic and friendly fitness chatbot. 

Your personality:
- Encouraging and motivational
- Uses fitness emojis appropriately  
- Celebrates user achievements
- Provides helpful fitness advice
- Speaks naturally and conversationally

Based on the conversation history, user's message, intent, and the action result, generate a natural, personalized response.
Keep responses concise but engaging (2-3 sentences max unless it's help/stats content).
Reference previous conversations when relevant to provide continuity.

You can use <think> tags to reason through your response, but only the content after </think> will be shown to the user."""

        user_prompt = f"""
User message: "{user_message}"
Intent: {intent}
Action result: {action_result}

Generate a natural, encouraging response as Pili:"""

        try:
            # Build messages including conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if available (limit to last 8 messages to avoid token limits)
            if conversation_history:
                recent_history = conversation_history[-8:]  # Keep last 8 messages for context
                for msg in recent_history:
                    if hasattr(msg, 'type'):
                        # Convert langchain message format
                        role = "user" if msg.type == "human" else "assistant"
                        messages.append({"role": role, "content": msg.content})
            
            # Add current prompt
            messages.append({"role": "user", "content": user_prompt})
            
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 200,
                "stream": True,  # Enable streaming
                "extra_body": {
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            }
            
            if self.provider == "ollama":
                params["stream"] = True
            
            response_stream = self.client.chat.completions.create(**params)
            
            content_buffer = ""
            thinking_mode = False
            
            for chunk in response_stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_buffer += delta.content
                        
                        # Handle thinking tags
                        if "<think>" in content_buffer and not thinking_mode:
                            thinking_mode = True
                            continue
                        
                        if "</think>" in content_buffer and thinking_mode:
                            # Extract content after </think>
                            parts = content_buffer.split("</think>")
                            if len(parts) > 1:
                                final_content = parts[-1]
                                # Yield the content after </think>
                                if final_content.strip():
                                    yield final_content
                            thinking_mode = False
                            content_buffer = ""
                            continue
                        
                        # If not in thinking mode, yield the content
                        if not thinking_mode:
                            yield delta.content
            
        except Exception as timeout_e:
            if "timeout" in str(timeout_e).lower():
                print(f"LLM streaming response timed out for intent: {intent}")
            # Fallback to non-streaming action result
            words = action_result.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield f" {word}"
                time.sleep(0.02)
                
        except Exception as e:
            print(f"LLM streaming response failed: {e}")
            # Fallback to non-streaming action result
            words = action_result.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield f" {word}"
                time.sleep(0.02)

    def _extract_intent_from_text(self, content: str, user_message: str) -> Dict[str, Any]:
        """Extract intent from text response when JSON parsing fails."""
        content_lower = content.lower()
        
        # Prioritize help intent detection first
        if "help" in content_lower:
            return {"intent": "help", "confidence": 0.8, "extracted_info": {}}
        elif "club" in content_lower:
            return {"intent": "manage_clubs", "confidence": 0.7, "extracted_info": {}}
        elif "challenge" in content_lower:
            return {"intent": "manage_challenges", "confidence": 0.7, "extracted_info": {}}
        elif "stats" in content_lower or "progress" in content_lower:
            return {"intent": "get_stats", "confidence": 0.7, "extracted_info": {}}
        elif "log_activity" in content_lower or "activity" in content_lower:
            return {"intent": "log_activity", "confidence": 0.7, "extracted_info": {}}
        else:
            return self._fallback_intent_detection(user_message)
    
    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Fallback rule-based intent detection."""
        message_lower = message.lower()
        
        # Activity logging intents
        if any(word in message_lower for word in ["did", "completed", "finished", "ran", "cycled", "swam", "walked", "workout"]):
            return {"intent": "log_activity", "confidence": 0.8, "extracted_info": {}}
        
        # Club management intents
        elif any(word in message_lower for word in ["club", "join club", "create club", "clubs"]):
            return {"intent": "manage_clubs", "confidence": 0.8, "extracted_info": {}}
        
        # Challenge management intents
        elif any(word in message_lower for word in ["challenge", "challenges", "create challenge", "join challenge"]):
            return {"intent": "manage_challenges", "confidence": 0.8, "extracted_info": {}}
        
        # Stats and progress intents
        elif any(word in message_lower for word in ["stats", "statistics", "progress", "summary", "activities", "history"]):
            return {"intent": "get_stats", "confidence": 0.8, "extracted_info": {}}
        
        # Help intent
        elif any(word in message_lower for word in ["help", "what can you do", "commands"]):
            return {"intent": "help", "confidence": 0.9, "extracted_info": {}}
        
        else:
            return {"intent": "unknown", "confidence": 0.5, "extracted_info": {}}

    def _extract_final_response(self, content: str) -> str:
        """Extract the final response after </think> tags."""
        if "</think>" in content:
            # Split by </think> and take the content after it
            parts = content.split("</think>")
            if len(parts) > 1:
                # Extract thinking process for debugging
                thinking_part = content.split("</think>")[-1].strip()
                if thinking_part.startswith("<think>"):
                    thinking_content = thinking_part[7:]  # Remove <think> tag
                    print(f"LLM Thinking Process: {thinking_content.strip()}")
                
                # Get everything after the last </think> tag
                final_response = parts[-1].strip()
                
                # Remove any leading newlines or whitespace
                final_response = final_response.lstrip('\n ').rstrip()
                
                return final_response if final_response else content
        
        # If no </think> tag found, return the original content
        return content
    
    def extract_thinking_process(self, content: str) -> tuple[str, str]:
        """Extract both thinking process and final response separately."""
        thinking = ""
        response = content
        
        if "<think>" in content and "</think>" in content:
            # Extract thinking content
            think_start = content.find("<think>") + 7
            think_end = content.find("</think>")
            if think_start > 6 and think_end > think_start:
                thinking = content[think_start:think_end].strip()
            
            # Extract final response
            response_start = content.find("</think>") + 8
            response = content[response_start:].strip()
        
        return thinking, response

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the LLM provider."""
        if not self.client:
            return {"status": "error", "message": "No LLM client configured"}
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
            return {
                "status": "success", 
                "provider": self.provider,
                "model": self.model,
                "message": "Connection successful"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": self.provider,
                "model": self.model,
                "message": str(e)
            }

# Create global LLM service instance
llm_service = LLMService() 