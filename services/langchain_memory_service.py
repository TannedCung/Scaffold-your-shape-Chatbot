"""LangChain-based memory service for conversation history management."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import asyncio
import json
from pathlib import Path
from collections import defaultdict
import logging

# Using basic LangChain message history without deprecated memory classes
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
        self._llm = None  # Lazy initialization
    
    def _get_llm(self):
        """Get LLM instance with lazy initialization."""
        if self._llm is None:
            # Fix LangChain verbose issue
            import langchain
            if not hasattr(langchain, 'verbose'):
                langchain.verbose = False
            
            app_config = get_configuration()
            if app_config.llm_provider == "openai":
                self._llm = ChatOpenAI(
                    model=app_config.openai_model,
                    api_key=app_config.openai_api_key,
                    temperature=0.3
                )
            else:
                self._llm = ChatOpenAI(
                    model=app_config.local_llm_model,
                    base_url=app_config.local_llm_base_url,
                    api_key=app_config.local_llm_api_key or "dummy-key",
                    temperature=0.3
                )
        return self._llm
    
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
    
    def get_chat_history_for_user(self, user_id: str, session_id: str = "default") -> FileChatMessageHistory:
        """Get or create chat history instance for a user."""
        memory_key = self._get_memory_key(user_id, session_id)
        
        if memory_key not in self.user_memories:
            chat_history_file = self._get_chat_history_file(user_id, session_id)
            
            # Ensure the file exists and has valid JSON content
            file_path = Path(chat_history_file)
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("[]", encoding="utf-8")
            elif file_path.read_text(encoding="utf-8").strip() == "":
                file_path.write_text("[]", encoding="utf-8")
                
            chat_history = FileChatMessageHistory(file_path=chat_history_file)
            
            self.user_memories[memory_key] = {
                "chat_history": chat_history,
                "created_at": datetime.now(timezone.utc),
                "last_accessed": datetime.now(timezone.utc),
                "user_id": user_id,
                "session_id": session_id
            }
        
        # Update last accessed time
        self.user_memories[memory_key]["last_accessed"] = datetime.now(timezone.utc)
        return self.user_memories[memory_key]["chat_history"]
    
    async def add_exchange(self, user_id: str, user_message: str, ai_response: str, session_id: str = "default"):
        """Add a user-AI exchange to memory."""
        chat_history = self.get_chat_history_for_user(user_id, session_id)
        
        # Add messages to chat history
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._add_messages_to_history(chat_history, user_message, ai_response)
        )
    
    def _add_messages_to_history(self, chat_history: FileChatMessageHistory, user_message: str, ai_response: str):
        """Add messages to chat history synchronously."""
        chat_history.add_user_message(user_message)
        chat_history.add_ai_message(ai_response)
    
    async def get_conversation_context(self, user_id: str, session_id: str = "default") -> str:
        """Get conversation context as formatted string for LLM."""
        chat_history = self.get_chat_history_for_user(user_id, session_id)
        
        try:
            # Get messages from chat history
            messages = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chat_history.messages
            )
            
            if not messages:
                return ""
            
            # Format the conversation history (last 10 messages)
            context_parts = []
            recent_messages = messages[-10:] if len(messages) > 10 else messages
            
            for message in recent_messages:
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
        chat_history = self.get_chat_history_for_user(user_id, session_id)
        
        try:
            messages = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chat_history.messages
            )
            return {"chat_history": messages}
        except Exception as e:
            logger.error(f"Error loading memory variables for {user_id}/{session_id}: {e}")
            return {"chat_history": []}
    
    async def clear_user_memory(self, user_id: str, session_id: Optional[str] = None):
        """Clear memory for a user."""
        if session_id:
            memory_key = self._get_memory_key(user_id, session_id)
            if memory_key in self.user_memories:
                # Clear the chat history
                chat_history = self.user_memories[memory_key]["chat_history"]
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chat_history.clear()
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
                chat_history = self.user_memories[key]["chat_history"]
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chat_history.clear()
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
        chat_history = memory_info["chat_history"]
        
        try:
            # Get message count from chat history
            messages = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chat_history.messages
            )
            
            message_count = len(messages)
            
            return {
                "user_id": user_id,
                "session_id": session_id,
                "has_memory": True,
                "message_count": message_count,
                "created_at": memory_info["created_at"],
                "last_accessed": memory_info["last_accessed"],
                "memory_type": "FileChatMessageHistory"
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
                chat_history = memory_info["chat_history"]
                messages = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chat_history.messages
                )
                
                total_messages += len(messages)
                
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
                chat_history = session_info["chat_history"]
                messages = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chat_history.messages
                )
                
                for i, message in enumerate(messages):
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
        chat_history = memory_info["chat_history"]
        
        try:
            messages = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chat_history.messages
            )
            
            # Apply limit
            if limit and len(messages) > limit:
                messages = messages[-limit:]
            
            # Format messages
            formatted_messages = []
            for message in messages:
                formatted_messages.append({
                    "role": "user" if isinstance(message, HumanMessage) else "assistant",
                    "content": message.content,
                    "timestamp": getattr(message, 'timestamp', None) or datetime.now(timezone.utc).isoformat()
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
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.max_conversation_age_days)
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