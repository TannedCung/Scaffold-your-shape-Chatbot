"""Integration tests for the agent system with memory."""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from agents.agent import PiliAgentSystem
from services.langchain_memory_service import LangChainMemoryService
from models.memory import MemoryConfiguration
from config.settings import get_configuration


class TestAgentMemoryIntegration:
    """Integration tests for agent system with memory."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_config(self):
        """Create test configuration."""
        with patch('config.settings.get_configuration') as mock_config:
            mock_config.return_value = MagicMock(
                memory_enabled=True,
                memory_max_messages_per_user=50,
                memory_max_characters_per_message=1000,
                memory_cleanup_interval_hours=1,
                memory_max_conversation_age_days=7,
                memory_enable_compression=True,
                memory_storage_backend="file",
                memory_type="buffer_window",
                llm_provider="openai",
                openai_model="gpt-3.5-turbo",
                openai_api_key="test-key"
            )
            yield mock_config.return_value
    
    @pytest.fixture
    def agent_system(self, temp_dir, test_config):
        """Create agent system for testing."""
        with patch('services.langchain_memory_service.langchain_memory_service') as mock_memory:
            # Create a real memory service for testing
            memory_service = LangChainMemoryService()
            memory_service.memory_dir = temp_dir / "test_memory"
            memory_service.memory_dir.mkdir(parents=True, exist_ok=True)
            mock_memory.return_value = memory_service
            
            system = PiliAgentSystem()
            yield system, memory_service
    
    @pytest.mark.asyncio
    async def test_memory_initialization(self, agent_system):
        """Test that memory service is properly initialized."""
        system, memory_service = agent_system
        
        # Test memory initialization
        await system._ensure_memory_initialized()
        assert system.memory_initialized is True
    
    @pytest.mark.asyncio
    async def test_user_memory_stats(self, agent_system):
        """Test getting user memory statistics."""
        system, memory_service = agent_system
        
        user_id = "test_user"
        
        # Get stats for user with no memory
        stats = await system.get_user_memory_stats(user_id)
        assert stats["has_memory"] is False
        
        # Add some memory
        await memory_service.add_exchange(user_id, "Hello", "Hi there!")
        
        # Get stats again
        stats = await system.get_user_memory_stats(user_id)
        assert stats["has_memory"] is True
        assert stats["message_count"] == 2
    
    @pytest.mark.asyncio
    async def test_clear_user_memory(self, agent_system):
        """Test clearing user memory through agent system."""
        system, memory_service = agent_system
        
        user_id = "test_user"
        
        # Add some memory
        await memory_service.add_exchange(user_id, "Test", "Response")
        
        # Verify memory exists
        stats_before = await system.get_user_memory_stats(user_id)
        assert stats_before["has_memory"] is True
        
        # Clear memory through agent system
        result = await system.clear_user_memory(user_id)
        assert result["success"] is True
        
        # Verify memory is cleared
        stats_after = await system.get_user_memory_stats(user_id)
        assert stats_after["has_memory"] is False
    
    @pytest.mark.asyncio
    async def test_process_request_with_memory_disabled(self, agent_system):
        """Test processing request when memory is disabled."""
        system, memory_service = agent_system
        
        with patch('config.settings.get_configuration') as mock_config:
            mock_config.return_value.memory_enabled = False
            
            # Mock the agent system to avoid actual LLM calls
            with patch.object(system, 'get_agent_for_user') as mock_get_agent:
                mock_agent = MagicMock()
                mock_result = {
                    "messages": [
                        MagicMock(content="Test response", name="assistant")
                    ]
                }
                mock_agent.ainvoke.return_value = mock_result
                mock_get_agent.return_value = mock_agent
                
                with patch.object(system, '_finalize_response') as mock_finalize:
                    mock_finalize.return_value = {
                        "response": "Test response",
                        "logs": [],
                        "finalized": True
                    }
                    
                    result = await system.process_request("test_user", "Hello")
                    assert result["response"] == "Test response"
    
    @pytest.mark.asyncio
    async def test_memory_context_injection(self, agent_system):
        """Test that conversation context is injected into agent processing."""
        system, memory_service = agent_system
        
        user_id = "test_user"
        session_id = "test_session"
        
        # Add some conversation history
        await memory_service.add_exchange(user_id, "I want to start running", "Great choice!", session_id)
        
        # Get conversation context
        context = await memory_service.get_conversation_context(user_id, session_id)
        
        assert "## Previous Conversation:" in context
        assert "I want to start running" in context
        assert "Great choice!" in context
    
    @pytest.mark.asyncio
    async def test_session_separation(self, agent_system):
        """Test that different sessions maintain separate memory."""
        system, memory_service = agent_system
        
        user_id = "test_user"
        session1 = "workout_session"
        session2 = "nutrition_session"
        
        # Add different conversations to different sessions
        await memory_service.add_exchange(user_id, "Plan my workout", "Let's create a plan!", session1)
        await memory_service.add_exchange(user_id, "What should I eat?", "Here's nutrition advice", session2)
        
        # Test that sessions are separate
        stats1 = await memory_service.get_user_memory_stats(user_id, session1)
        stats2 = await memory_service.get_user_memory_stats(user_id, session2)
        
        assert stats1["session_id"] == session1
        assert stats2["session_id"] == session2
        assert stats1["message_count"] == 2
        assert stats2["message_count"] == 2
        
        # Clear one session, other should remain
        await memory_service.clear_user_memory(user_id, session1)
        
        stats1_after = await memory_service.get_user_memory_stats(user_id, session1)
        stats2_after = await memory_service.get_user_memory_stats(user_id, session2)
        
        assert stats1_after["has_memory"] is False
        assert stats2_after["has_memory"] is True
    
    @pytest.mark.asyncio
    async def test_agent_cache_management(self, agent_system):
        """Test agent caching and cleanup."""
        system, memory_service = agent_system
        
        user_id = "test_user"
        
        # Mock agent creation to avoid actual initialization
        with patch('agents.agent.create_agent_swarm') as mock_create:
            mock_agent = MagicMock()
            mock_mcp_client = MagicMock()
            mock_create.return_value = (mock_agent, mock_mcp_client)
            
            # Get agent for user (should create cache entry)
            agent = await system.get_agent_for_user(user_id)
            assert user_id in system.agent_cache
            
            # Clear cache for user
            await system.clear_user_cache(user_id)
            assert user_id not in system.agent_cache
    
    @pytest.mark.asyncio 
    async def test_memory_error_handling(self, agent_system):
        """Test error handling in memory operations."""
        system, memory_service = agent_system
        
        # Test error handling when memory operation fails
        with patch.object(memory_service, 'add_exchange', side_effect=Exception("Memory error")):
            result = await system.clear_user_memory("nonexistent_user")
            # Should handle gracefully
            assert "success" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_access(self, agent_system):
        """Test concurrent access to memory service."""
        system, memory_service = agent_system
        
        user_id = "test_user"
        
        # Create multiple concurrent memory operations
        tasks = []
        for i in range(5):
            task = memory_service.add_exchange(user_id, f"Message {i}", f"Response {i}")
            tasks.append(task)
        
        # Execute all tasks concurrently
        await asyncio.gather(*tasks)
        
        # Verify all messages were added
        stats = await memory_service.get_user_memory_stats(user_id)
        assert stats["message_count"] == 10  # 5 exchanges = 10 messages
    
    @pytest.mark.asyncio
    async def test_memory_configuration_integration(self, agent_system):
        """Test that memory configuration is properly integrated."""
        system, memory_service = agent_system
        
        # Test that configuration is applied
        assert memory_service.config is not None
        assert memory_service.config.max_messages_per_user > 0
        
        # Test memory directory creation
        assert memory_service.memory_dir.exists()
    
    def test_format_user_message_with_context(self):
        """Test user message formatting with context."""
        from agents.agent import format_user_message_with_context
        
        user_id = "test_user"
        message = "Hello"
        
        formatted = format_user_message_with_context(user_id, message)
        
        assert f"[UserId: {user_id}]" in formatted
        assert message in formatted
        assert "[Time:" in formatted


# Test configuration for pytest
if __name__ == "__main__":
    pytest.main([__file__]) 