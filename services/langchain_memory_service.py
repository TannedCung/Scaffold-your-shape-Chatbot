"""LangChain-based memory service for conversation history management."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path
from collections import defaultdict
import logging

from langchain.memory.buffer import ConversationBufferMemory
from langchain.memory.summary_buffer import ConversationSummaryBufferMemory
from langchain.memory.buffer_window import ConversationBufferWindowMemory
from langchain.memory.entity import ConversationEntityMemory
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config.settings import get_configuration
from models.memory import MemoryConfiguration, MemoryStats

logger = logging.getLogger(__name__)

class LangChainMemoryService:
    """Service for managing conversation memory using LangChain's memory capabilities."""
    
    def __init__(self, config: Optional[MemoryConfiguration] = None):
        self.config = config or MemoryConfiguration()
        self.user_memories: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.memory_dir = Path("data/langchain_memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_task = None
        
        # Initialize LLM for summary-based memory
        app_config = get_configuration()
        if app_config.llm_provider == "openai":
            self.llm = ChatOpenAI(
                model=app_config.openai_model,
                api_key=app_config.openai_api_key,
                temperature=0.3
            )
        else:
            self.llm = ChatOpenAI(
                model=app_config.local_llm_model,
                base_url=app_config.local_llm_base_url,
                api_key=app_config.local_llm_api_key or "dummy-key",
                temperature=0.3
            )
    
    async def initialize(self):
        """Initialize the memory service."""
        # Start cleanup task
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
    async def shutdown(self):
        """Shutdown the memory service."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    def _get_memory_key(self, user_id: str, session_id: str = "default") -> str:
        """Generate a unique key for user memory."""
        return f"{user_id}_{session_id}"
    
    def _get_chat_history_file(self, user_id: str, session_id: str = "default") -> str:
        """Get the file path for storing chat history."""
        return str(self.memory_dir / f"{user_id}_{session_id}_history.json")
    
    def get_memory_for_user(self, user_id: str, session_id: str = "default", memory_type: str = "buffer_window") -> Any:
        """Get or create memory instance for a user."""
        memory_key = self._get_memory_key(user_id, session_id)
        
        if memory_key not in self.user_memories:
            chat_history_file = self._get_chat_history_file(user_id, session_id)
            chat_history = FileChatMessageHistory(file_path=chat_history_file)
            
            # Create different types of memory based on configuration
            if memory_type == "buffer":
                memory = ConversationBufferMemory(
                    chat_memory=chat_history,
                    memory_key="chat_history",
                    input_key="input",
                    output_key="output",
                    return_messages=True,
                    max_token_limit=self.config.max_characters_per_message * 10
                )
            elif memory_type == "buffer_window":
                memory = ConversationBufferWindowMemory(
                    chat_memory=chat_history,
                    memory_key="chat_history",
                    input_key="input",
                    output_key="output",
                    return_messages=True,
                    k=min(self.config.max_messages_per_user // 2, 20)  # Keep last 20 exchanges
                )
            elif memory_type == "summary_buffer":
                memory = ConversationSummaryBufferMemory(
                    llm=self.llm,
                    chat_memory=chat_history,
                    memory_key="chat_history",
                    input_key="input",
                    output_key="output",
                    return_messages=True,
                    max_token_limit=2000,
                    moving_summary_buffer=""
                )
            elif memory_type == "entity":
                memory = ConversationEntityMemory(
                    llm=self.llm,
                    chat_memory=chat_history,
                    memory_key="chat_history",
                    input_key="input",
                    output_key="output",
                    return_messages=True
                )
            else:
                # Default to buffer window
                memory = ConversationBufferWindowMemory(
                    chat_memory=chat_history,
                    memory_key="chat_history",
                    input_key="input",
                    output_key="output",
                    return_messages=True,
                    k=20
                )
            
            self.user_memories[memory_key] = {
                "memory": memory,
                "created_at": datetime.utcnow(),
                "last_accessed": datetime.utcnow(),
                "user_id": user_id,
                "session_id": session_id
            }
        
        # Update last accessed time
        self.user_memories[memory_key]["last_accessed"] = datetime.utcnow()
        return self.user_memories[memory_key]["memory"]
    
    async def add_exchange(self, user_id: str, user_message: str, ai_response: str, session_id: str = "default"):
        """Add a user-AI exchange to memory."""
        memory = self.get_memory_for_user(user_id, session_id)
        
        # Save the conversation exchange
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: memory.save_context(
                {"input": user_message},
                {"output": ai_response}
            )
        )
    
    async def get_conversation_context(self, user_id: str, session_id: str = "default") -> str:
        """Get conversation context as formatted string for LLM."""
        memory = self.get_memory_for_user(user_id, session_id)
        
        try:
            # Load memory variables in executor to avoid blocking
            memory_variables = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: memory.load_memory_variables({})
            )
            
            chat_history = memory_variables.get("chat_history", [])
            
            if not chat_history:
                return ""
            
            # Format the conversation history
            context_parts = []
            for message in chat_history[-10:]:  # Last 10 messages
                if isinstance(message, HumanMessage):
                    context_parts.append(f"User: {message.content}")
                elif isinstance(message, AIMessage):
                    context_parts.append(f"Assistant: {message.content}")
                elif isinstance(message, SystemMessage):
                    context_parts.append(f"System: {message.content}")
            
            if context_parts:
                return "## Previous Conversation:\n" + "\n".join(context_parts) + "\n\n"
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting conversation context for {user_id}/{session_id}: {e}")
            return ""
    
    async def get_memory_variables(self, user_id: str, session_id: str = "default") -> Dict[str, Any]:
        """Get memory variables for a user that can be used in prompts."""
        memory = self.get_memory_for_user(user_id, session_id)
        
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: memory.load_memory_variables({})
            )
        except Exception as e:
            logger.error(f"Error loading memory variables for {user_id}/{session_id}: {e}")
            return {}
    
    async def clear_user_memory(self, user_id: str, session_id: Optional[str] = None):
        """Clear memory for a user."""
        if session_id:
            memory_key = self._get_memory_key(user_id, session_id)
            if memory_key in self.user_memories:
                # Clear the memory
                memory = self.user_memories[memory_key]["memory"]
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: memory.clear()
                )
                del self.user_memories[memory_key]
            
            # Remove history file
            history_file = Path(self._get_chat_history_file(user_id, session_id))
            if history_file.exists():
                history_file.unlink()
        else:
            # Clear all sessions for user
            keys_to_remove = [
                key for key in self.user_memories.keys() 
                if self.user_memories[key]["user_id"] == user_id
            ]
            
            for key in keys_to_remove:
                memory = self.user_memories[key]["memory"]
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: memory.clear()
                )
                del self.user_memories[key]
            
            # Remove history files
            for file_path in self.memory_dir.glob(f"{user_id}_*_history.json"):
                file_path.unlink()
    
    async def get_user_memory_stats(self, user_id: str, session_id: str = "default") -> Dict[str, Any]:
        """Get memory statistics for a specific user."""
        memory_key = self._get_memory_key(user_id, session_id)
        
        if memory_key not in self.user_memories:
            return {
                "user_id": user_id,
                "session_id": session_id,
                "has_memory": False,
                "message_count": 0
            }
        
        memory_info = self.user_memories[memory_key]
        memory = memory_info["memory"]
        
        try:
            # Get message count from chat history
            memory_vars = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: memory.load_memory_variables({})
            )
            
            chat_history = memory_vars.get("chat_history", [])
            message_count = len(chat_history)
            
            return {
                "user_id": user_id,
                "session_id": session_id,
                "has_memory": True,
                "message_count": message_count,
                "created_at": memory_info["created_at"],
                "last_accessed": memory_info["last_accessed"],
                "memory_type": type(memory).__name__
            }
            
        except Exception as e:
            return {
                "user_id": user_id,
                "session_id": session_id,
                "has_memory": True,
                "error": str(e)
            }
    
    async def get_global_memory_stats(self) -> MemoryStats:
        """Get global memory statistics."""
        total_users = len(set(info["user_id"] for info in self.user_memories.values()))
        total_conversations = len(self.user_memories)
        total_messages = 0
        
        oldest_conversation = None
        newest_conversation = None
        
        for memory_info in self.user_memories.values():
            try:
                memory = memory_info["memory"]
                memory_vars = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: memory.load_memory_variables({})
                )
                
                chat_history = memory_vars.get("chat_history", [])
                total_messages += len(chat_history)
                
                created_at = memory_info["created_at"]
                if oldest_conversation is None or created_at < oldest_conversation:
                    oldest_conversation = created_at
                    
                last_accessed = memory_info["last_accessed"]
                if newest_conversation is None or last_accessed > newest_conversation:
                    newest_conversation = last_accessed
                    
            except Exception as e:
                logger.error(f"Error getting stats for memory: {e}")
        
        # Estimate memory size (rough calculation)
        memory_size_mb = len(json.dumps(str(self.user_memories))) / (1024 * 1024)
        
        return MemoryStats(
            total_users=total_users,
            total_conversations=total_conversations,
            total_messages=total_messages,
            memory_size_mb=memory_size_mb,
            oldest_conversation=oldest_conversation,
            newest_conversation=newest_conversation
        )
    
    async def search_conversations(self, user_id: str, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search through conversation history (basic text search)."""
        results = []
        query_lower = query.lower()
        
        # Get all sessions for this user
        user_sessions = [
            info for info in self.user_memories.values() 
            if info["user_id"] == user_id
        ]
        
        for session_info in user_sessions:
            try:
                memory = session_info["memory"]
                memory_vars = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: memory.load_memory_variables({})
                )
                
                chat_history = memory_vars.get("chat_history", [])
                
                for i, message in enumerate(chat_history):
                    if query_lower in message.content.lower():
                        results.append({
                            "session_id": session_info["session_id"],
                            "message_index": i,
                            "message_type": type(message).__name__,
                            "content": message.content,
                            "relevance_score": 1.0  # Simple binary relevance
                        })
                        
                        if len(results) >= max_results:
                            break
                            
            except Exception as e:
                logger.error(f"Error searching session {session_info['session_id']}: {e}")
        
        return results[:max_results]
    
    async def get_conversation_history_formatted(self, user_id: str, session_id: str = "default", limit: int = 50) -> Dict[str, Any]:
        """Get conversation history in a formatted structure."""
        memory_key = self._get_memory_key(user_id, session_id)
        
        if memory_key not in self.user_memories:
            return {
                "user_id": user_id,
                "session_id": session_id,
                "messages": [],
                "message_count": 0
            }
        
        memory_info = self.user_memories[memory_key]
        memory = memory_info["memory"]
        
        try:
            memory_vars = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: memory.load_memory_variables({})
            )
            
            chat_history = memory_vars.get("chat_history", [])
            
            # Apply limit
            if limit and len(chat_history) > limit:
                chat_history = chat_history[-limit:]
            
            # Format messages
            formatted_messages = []
            for message in chat_history:
                formatted_messages.append({
                    "role": "user" if isinstance(message, HumanMessage) else "assistant",
                    "content": message.content,
                    "timestamp": getattr(message, 'timestamp', None) or datetime.utcnow().isoformat()
                })
            
            return {
                "user_id": user_id,
                "session_id": session_id,
                "messages": formatted_messages,
                "message_count": len(formatted_messages),
                "created_at": memory_info["created_at"],
                "updated_at": memory_info["last_accessed"]
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation history for {user_id}/{session_id}: {e}")
            return {
                "user_id": user_id,
                "session_id": session_id,
                "messages": [],
                "message_count": 0,
                "error": str(e)
            }
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old conversations."""
        while True:
            try:
                await asyncio.sleep(self.config.memory_cleanup_interval_hours * 3600)
                await self._cleanup_old_conversations()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _cleanup_old_conversations(self):
        """Clean up conversations older than configured age."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.max_conversation_age_days)
        keys_to_remove = []
        
        for key, memory_info in self.user_memories.items():
            if memory_info["last_accessed"] < cutoff_date:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            memory_info = self.user_memories[key]
            user_id = memory_info["user_id"]
            session_id = memory_info["session_id"]
            
            await self.clear_user_memory(user_id, session_id)
            logger.info(f"Cleaned up old conversation for user {user_id}, session {session_id}")


# Global LangChain memory service instance
langchain_memory_service = LangChainMemoryService() 