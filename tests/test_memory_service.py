"""Unit tests for the LangChain memory service."""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from services.langchain_memory_service import LangChainMemoryService
from models.memory import MemoryConfiguration


class TestLangChainMemoryService:
    """Test cases for LangChain memory service."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory_config(self):
        """Create a test memory configuration."""
        return MemoryConfiguration(
            max_messages_per_user=50,
            max_characters_per_message=1000,
            memory_cleanup_interval_hours=1,
            max_conversation_age_days=7,
            enable_memory_compression=True,
            memory_storage_backend="file"
        )
    
    @pytest.fixture
    def memory_service(self, temp_dir, memory_config):
        """Create a memory service instance for testing."""
        service = LangChainMemoryService(memory_config)
        service.memory_dir = temp_dir / "test_memory"
        service.memory_dir.mkdir(parents=True, exist_ok=True)
        return service
    
    @pytest.mark.asyncio
    async def test_initialization(self, memory_service):
        """Test memory service initialization."""
        await memory_service.initialize()
        assert memory_service.config is not None
        assert memory_service.memory_dir.exists()
    
    @pytest.mark.asyncio
    async def test_get_chat_history_for_user(self, memory_service):
        """Test getting chat history for a user."""
        user_id = "test_user"
        session_id = "test_session"
        
        chat_history = memory_service.get_chat_history_for_user(user_id, session_id)
        assert chat_history is not None
        
        # Check that user memory is created
        memory_key = memory_service._get_memory_key(user_id, session_id)
        assert memory_key in memory_service.user_memories
        
        memory_info = memory_service.user_memories[memory_key]
        assert memory_info["user_id"] == user_id
        assert memory_info["session_id"] == session_id
        assert "created_at" in memory_info
        assert "last_accessed" in memory_info
    
    @pytest.mark.asyncio
    async def test_add_exchange(self, memory_service):
        """Test adding a conversation exchange."""
        user_id = "test_user"
        session_id = "test_session"
        user_message = "Hello, I want to start exercising"
        ai_response = "Great! I'm Pili, your fitness assistant. Let's get started! 💪"
        
        await memory_service.add_exchange(user_id, user_message, ai_response, session_id)
        
        # Verify messages were added
        chat_history = memory_service.get_chat_history_for_user(user_id, session_id)
        messages = chat_history.messages
        
        assert len(messages) == 2  # User message + AI response
        assert messages[0].content == user_message
        assert messages[1].content == ai_response
    
    @pytest.mark.asyncio
    async def test_get_conversation_context(self, memory_service):
        """Test getting conversation context."""
        user_id = "test_user"
        session_id = "test_session"
        
        # Add some conversation history
        await memory_service.add_exchange(user_id, "Hi", "Hello!", session_id)
        await memory_service.add_exchange(user_id, "I want to run", "That's great!", session_id)
        
        context = await memory_service.get_conversation_context(user_id, session_id)
        
        assert "## Previous Conversation:" in context
        assert "User: Hi" in context
        assert "Assistant: Hello!" in context
        assert "User: I want to run" in context
        assert "Assistant: That's great!" in context
    
    @pytest.mark.asyncio
    async def test_get_user_memory_stats(self, memory_service):
        """Test getting user memory statistics."""
        user_id = "test_user"
        session_id = "test_session"
        
        # Test with no memory
        stats = await memory_service.get_user_memory_stats(user_id, session_id)
        assert stats["has_memory"] is False
        assert stats["message_count"] == 0
        
        # Add some messages
        await memory_service.add_exchange(user_id, "Hello", "Hi there!", session_id)
        
        stats = await memory_service.get_user_memory_stats(user_id, session_id)
        assert stats["has_memory"] is True
        assert stats["message_count"] == 2
        assert stats["user_id"] == user_id
        assert stats["session_id"] == session_id
        assert stats["memory_type"] == "FileChatMessageHistory"
    
    @pytest.mark.asyncio
    async def test_clear_user_memory(self, memory_service):
        """Test clearing user memory."""
        user_id = "test_user"
        session_id = "test_session"
        
        # Add some memory
        await memory_service.add_exchange(user_id, "Test", "Response", session_id)
        
        # Verify memory exists
        stats_before = await memory_service.get_user_memory_stats(user_id, session_id)
        assert stats_before["has_memory"] is True
        
        # Clear memory
        await memory_service.clear_user_memory(user_id, session_id)
        
        # Verify memory is cleared
        stats_after = await memory_service.get_user_memory_stats(user_id, session_id)
        assert stats_after["has_memory"] is False


# Simple test to verify imports work
def test_imports():
    """Test that all imports work correctly."""
    from services.langchain_memory_service import LangChainMemoryService
    from models.memory import MemoryConfiguration
    assert LangChainMemoryService is not None
    assert MemoryConfiguration is not None 