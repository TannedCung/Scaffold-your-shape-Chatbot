"""Memory service for conversation history management."""

import json
import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
from models.memory import (
    ConversationMessage, ConversationHistory, MemoryConfiguration,
    MemoryStats, MemorySearchQuery, MemorySearchResult, MessageRole
)
from config.settings import get_configuration
import uuid
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing conversation memory and history."""
    
    def __init__(self, config: Optional[MemoryConfiguration] = None):
        self.config = config or MemoryConfiguration()
        self.conversations: Dict[str, Dict[str, ConversationHistory]] = defaultdict(dict)
        self.memory_dir = Path("data/memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_task = None
        
    async def initialize(self):
        """Initialize the memory service and load existing conversations."""
        if self.config.memory_storage_backend == "file":
            await self._load_conversations_from_files()
        
        # Start cleanup task
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
    async def shutdown(self):
        """Shutdown the memory service and save conversations."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        if self.config.memory_storage_backend == "file":
            await self._save_all_conversations()
    
    async def add_message(
        self, 
        user_id: str, 
        role: MessageRole, 
        content: str,
        session_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        agent_name: Optional[str] = None
    ) -> ConversationMessage:
        """Add a message to the conversation history."""
        
        # Truncate content if too long
        if len(content) > self.config.max_characters_per_message:
            content = content[:self.config.max_characters_per_message] + "... [truncated]"
        
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
            tool_calls=tool_calls,
            agent_name=agent_name
        )
        
        # Get or create conversation history
        if user_id not in self.conversations:
            self.conversations[user_id] = {}
            
        if session_id not in self.conversations[user_id]:
            self.conversations[user_id][session_id] = ConversationHistory(
                user_id=user_id,
                session_id=session_id
            )
        
        conversation = self.conversations[user_id][session_id]
        conversation.messages.append(message)
        conversation.updated_at = datetime.utcnow()
        
        # Trim conversation if too long
        if len(conversation.messages) > self.config.max_messages_per_user:
            # Keep the most recent messages
            excess = len(conversation.messages) - self.config.max_messages_per_user
            conversation.messages = conversation.messages[excess:]
        
        # Save to storage if using file backend
        if self.config.memory_storage_backend == "file":
            await self._save_conversation(user_id, session_id)
            
        return message
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        session_id: str = "default",
        limit: Optional[int] = None
    ) -> Optional[ConversationHistory]:
        """Get conversation history for a user and session."""
        
        if user_id not in self.conversations or session_id not in self.conversations[user_id]:
            return None
            
        conversation = self.conversations[user_id][session_id]
        
        if limit and len(conversation.messages) > limit:
            # Return a copy with limited messages
            limited_conversation = conversation.copy()
            limited_conversation.messages = conversation.messages[-limit:]
            return limited_conversation
            
        return conversation
    
    async def get_recent_messages(
        self, 
        user_id: str, 
        session_id: str = "default",
        count: int = 10
    ) -> List[ConversationMessage]:
        """Get the most recent messages for context."""
        
        conversation = await self.get_conversation_history(user_id, session_id)
        if not conversation:
            return []
            
        return conversation.messages[-count:] if conversation.messages else []
    
    async def get_conversation_context(
        self, 
        user_id: str, 
        session_id: str = "default",
        max_tokens: int = 4000
    ) -> str:
        """Get conversation context as formatted string for LLM."""
        
        recent_messages = await self.get_recent_messages(user_id, session_id, count=20)
        if not recent_messages:
            return ""
        
        context_parts = []
        current_tokens = 0
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        for message in reversed(recent_messages):
            message_text = f"{message.role.value}: {message.content}"
            estimated_tokens = len(message_text) // 4
            
            if current_tokens + estimated_tokens > max_tokens:
                break
                
            context_parts.insert(0, message_text)
            current_tokens += estimated_tokens
        
        if context_parts:
            return "## Previous Conversation:\n" + "\n".join(context_parts) + "\n\n"
        
        return ""
    
    async def search_conversations(
        self, 
        query: MemorySearchQuery
    ) -> List[MemorySearchResult]:
        """Search through conversation history."""
        
        results = []
        
        if query.user_id not in self.conversations:
            return results
        
        # Simple text-based search (can be enhanced with vector search later)
        search_terms = query.query.lower().split()
        
        for session_id, conversation in self.conversations[query.user_id].items():
            for i, message in enumerate(conversation.messages):
                # Check date filters
                if query.date_from and message.timestamp < query.date_from:
                    continue
                if query.date_to and message.timestamp > query.date_to:
                    continue
                
                # Calculate relevance score
                content_lower = message.content.lower()
                relevance_score = 0.0
                
                for term in search_terms:
                    if term in content_lower:
                        relevance_score += 1.0
                
                if relevance_score > 0:
                    # Get context messages (surrounding messages)
                    context_start = max(0, i - 2)
                    context_end = min(len(conversation.messages), i + 3)
                    context_messages = conversation.messages[context_start:context_end]
                    
                    result = MemorySearchResult(
                        user_id=query.user_id,
                        session_id=session_id,
                        message=message,
                        relevance_score=relevance_score / len(search_terms),
                        context_messages=context_messages if query.include_content else []
                    )
                    results.append(result)
        
        # Sort by relevance and limit results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:query.max_results]
    
    async def clear_user_memory(self, user_id: str, session_id: Optional[str] = None):
        """Clear memory for a user (optionally specific session)."""
        
        if user_id not in self.conversations:
            return
        
        if session_id:
            if session_id in self.conversations[user_id]:
                del self.conversations[user_id][session_id]
                # Remove file if using file storage
                if self.config.memory_storage_backend == "file":
                    file_path = self.memory_dir / f"{user_id}_{session_id}.json"
                    if file_path.exists():
                        file_path.unlink()
        else:
            # Clear all sessions for user
            if self.config.memory_storage_backend == "file":
                for session_id in list(self.conversations[user_id].keys()):
                    file_path = self.memory_dir / f"{user_id}_{session_id}.json"
                    if file_path.exists():
                        file_path.unlink()
            
            del self.conversations[user_id]
    
    async def get_memory_stats(self) -> MemoryStats:
        """Get statistics about memory usage."""
        
        total_users = len(self.conversations)
        total_conversations = sum(len(sessions) for sessions in self.conversations.values())
        total_messages = sum(
            len(conv.messages) 
            for sessions in self.conversations.values() 
            for conv in sessions.values()
        )
        
        # Estimate memory size
        memory_size = 0
        oldest_conversation = None
        newest_conversation = None
        
        for sessions in self.conversations.values():
            for conversation in sessions.values():
                # Rough size estimation
                conv_size = len(json.dumps(conversation.dict(), default=str))
                memory_size += conv_size
                
                if oldest_conversation is None or conversation.created_at < oldest_conversation:
                    oldest_conversation = conversation.created_at
                    
                if newest_conversation is None or conversation.updated_at > newest_conversation:
                    newest_conversation = conversation.updated_at
        
        return MemoryStats(
            total_users=total_users,
            total_conversations=total_conversations,
            total_messages=total_messages,
            memory_size_mb=memory_size / (1024 * 1024),
            oldest_conversation=oldest_conversation,
            newest_conversation=newest_conversation
        )
    
    async def _load_conversations_from_files(self):
        """Load conversations from JSON files."""
        
        try:
            for file_path in self.memory_dir.glob("*.json"):
                try:
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        conversation_data = json.loads(content)
                        conversation = ConversationHistory(**conversation_data)
                        
                        if conversation.user_id not in self.conversations:
                            self.conversations[conversation.user_id] = {}
                        
                        self.conversations[conversation.user_id][conversation.session_id] = conversation
                        
                except Exception as e:
                    logger.error(f"Error loading conversation from {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading conversations from files: {e}")
    
    async def _save_conversation(self, user_id: str, session_id: str):
        """Save a specific conversation to file."""
        
        if user_id not in self.conversations or session_id not in self.conversations[user_id]:
            return
            
        conversation = self.conversations[user_id][session_id]
        file_path = self.memory_dir / f"{user_id}_{session_id}.json"
        
        try:
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(conversation.dict(), default=str, indent=2))
        except Exception as e:
            logger.error(f"Error saving conversation {user_id}/{session_id}: {e}")
    
    async def _save_all_conversations(self):
        """Save all conversations to files."""
        
        tasks = []
        for user_id, sessions in self.conversations.items():
            for session_id in sessions.keys():
                task = self._save_conversation(user_id, session_id)
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
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
        users_to_remove = []
        
        for user_id, sessions in self.conversations.items():
            sessions_to_remove = []
            
            for session_id, conversation in sessions.items():
                if conversation.updated_at < cutoff_date:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                await self.clear_user_memory(user_id, session_id)
                logger.info(f"Cleaned up old conversation for user {user_id}, session {session_id}")
            
            if not sessions:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            if user_id in self.conversations:
                del self.conversations[user_id]


# Global memory service instance
memory_service = MemoryService() 