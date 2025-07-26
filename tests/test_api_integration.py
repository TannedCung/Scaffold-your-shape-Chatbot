"""API integration tests for the FastAPI endpoints."""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import json

from main import app
from services.langchain_memory_service import LangChainMemoryService


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_client(self, temp_dir):
        """Create test client with mocked dependencies."""
        memory_service = LangChainMemoryService()
        memory_service.memory_dir = temp_dir / "test_memory"
        memory_service.memory_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('config.settings.get_configuration') as mock_config:
            mock_config.return_value = MagicMock(
                memory_enabled=True,
                memory_max_messages_per_user=50,
                memory_max_characters_per_message=1000,
                memory_cleanup_interval_hours=1,
                memory_max_conversation_age_days=7,
                memory_enable_compression=True,
                memory_storage_backend="file",
                memory_type="buffer_window"
            )
            
            with patch('main.langchain_memory_service', memory_service):
                yield TestClient(app), memory_service
    
    def test_health_endpoint(self, test_client):
        """Test the health endpoint."""
        client, _ = test_client
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_chat_endpoint_basic(self, test_client):
        """Test basic chat endpoint functionality."""
        client, memory_service = test_client
        
        # Mock the agent system to avoid actual LLM calls
        with patch('agents.agent.agent_system') as mock_agent_system:
            mock_agent_system.process_request.return_value = {
                "response": "Hello! I'm Pili, your fitness assistant! 💪",
                "logs": [{"agent_system": "test", "status": "success"}]
            }
            
            response = client.post("/api/chat", json={
                "user_id": "test_user",
                "message": "Hello",
                "session_id": "test_session",
                "stream": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "logs" in data
            assert "Pili" in data["response"]
    
    def test_chat_endpoint_with_session(self, test_client):
        """Test chat endpoint with session ID."""
        client, memory_service = test_client
        
        with patch('agents.agent.agent_system') as mock_agent_system:
            mock_agent_system.process_request.return_value = {
                "response": "Got it!",
                "logs": []
            }
            
            response = client.post("/api/chat", json={
                "user_id": "test_user",
                "message": "Test message",
                "session_id": "custom_session",
                "stream": False
            })
            
            assert response.status_code == 200
            # Verify that the correct session ID was passed
            mock_agent_system.process_request.assert_called_with(
                "test_user", "Test message", "custom_session"
            )
    
    def test_chat_endpoint_streaming(self, test_client):
        """Test streaming chat endpoint."""
        client, memory_service = test_client
        
        with patch('agents.agent.agent_system') as mock_agent_system:
            mock_agent_system.process_request.return_value = {
                "response": "Streaming response",
                "logs": [],
                "chain_of_thought": [],
                "finalized": True
            }
            
            response = client.post("/api/chat", json={
                "user_id": "test_user",
                "message": "Hello",
                "stream": True
            })
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_memory_stats_endpoint(self, test_client):
        """Test memory statistics endpoint."""
        client, memory_service = test_client
        
        # Add some test memory
        asyncio.run(memory_service.add_exchange("test_user", "Hello", "Hi there!"))
        
        response = client.get("/api/memory/stats/test_user")
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == "test_user"
        assert data["has_memory"] is True
        assert data["message_count"] == 2
    
    def test_global_memory_stats_endpoint(self, test_client):
        """Test global memory statistics endpoint."""
        client, memory_service = test_client
        
        # Add some test memory for multiple users
        asyncio.run(memory_service.add_exchange("user1", "Hello", "Hi!"))
        asyncio.run(memory_service.add_exchange("user2", "Test", "Response"))
        
        response = client.get("/api/memory/global-stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["memory_enabled"] is True
        assert "stats" in data
        assert data["stats"]["total_users"] >= 2
        assert data["stats"]["total_messages"] >= 4
    
    def test_clear_memory_endpoint(self, test_client):
        """Test clear memory endpoint."""
        client, memory_service = test_client
        
        # Add some test memory
        asyncio.run(memory_service.add_exchange("test_user", "Hello", "Hi there!"))
        
        # Verify memory exists
        stats_before = asyncio.run(memory_service.get_user_memory_stats("test_user"))
        assert stats_before["has_memory"] is True
        
        # Clear memory
        response = client.post("/api/memory/clear", json={
            "user_id": "test_user",
            "session_id": "default"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify memory is cleared
        stats_after = asyncio.run(memory_service.get_user_memory_stats("test_user"))
        assert stats_after["has_memory"] is False
    
    def test_search_memory_endpoint(self, test_client):
        """Test memory search endpoint."""
        client, memory_service = test_client
        
        # Add some test conversations
        asyncio.run(memory_service.add_exchange("test_user", "I want to go running", "Great choice!"))
        asyncio.run(memory_service.add_exchange("test_user", "How about swimming?", "Swimming is excellent!"))
        asyncio.run(memory_service.add_exchange("test_user", "I prefer running", "Running it is!"))
        
        response = client.post("/api/memory/search", json={
            "user_id": "test_user",
            "query": "running",
            "max_results": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "running"
        assert data["results_count"] >= 2
        assert len(data["results"]) >= 2
        
        # Check that results contain "running"
        for result in data["results"]:
            assert "running" in result["content"].lower()
    
    def test_conversation_history_endpoint(self, test_client):
        """Test conversation history endpoint."""
        client, memory_service = test_client
        
        # Add some test conversation
        asyncio.run(memory_service.add_exchange("test_user", "Hello", "Hi there!"))
        asyncio.run(memory_service.add_exchange("test_user", "How are you?", "I'm great!"))
        
        response = client.get("/api/memory/conversation/test_user?session_id=default&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"
        assert data["session_id"] == "default"
        assert data["message_count"] == 4  # 2 exchanges = 4 messages
        assert len(data["messages"]) == 4
        
        # Check message structure
        first_message = data["messages"][0]
        assert first_message["role"] == "user"
        assert first_message["content"] == "Hello"
        assert "timestamp" in first_message
    
    def test_memory_disabled_endpoints(self, test_client):
        """Test endpoints when memory is disabled."""
        client, memory_service = test_client
        
        with patch('config.settings.get_configuration') as mock_config:
            mock_config.return_value.memory_enabled = False
            
            # Test global stats
            response = client.get("/api/memory/global-stats")
            assert response.status_code == 200
            data = response.json()
            assert data["memory_enabled"] is False
            
            # Test search
            response = client.post("/api/memory/search", json={
                "user_id": "test_user",
                "query": "test"
            })
            assert response.status_code == 503
            
            # Test conversation history
            response = client.get("/api/memory/conversation/test_user")
            assert response.status_code == 503
    
    def test_api_error_handling(self, test_client):
        """Test API error handling."""
        client, memory_service = test_client
        
        # Test invalid user ID in stats
        response = client.get("/api/memory/stats/")
        assert response.status_code == 404
        
        # Test invalid request body in clear memory
        response = client.post("/api/memory/clear", json={})
        assert response.status_code == 422  # Validation error
        
        # Test invalid search query
        response = client.post("/api/memory/search", json={
            "query": "test"  # Missing user_id
        })
        assert response.status_code == 422
    
    def test_chat_endpoint_validation(self, test_client):
        """Test chat endpoint request validation."""
        client, memory_service = test_client
        
        # Test missing user_id
        response = client.post("/api/chat", json={
            "message": "Hello"
        })
        assert response.status_code == 422
        
        # Test missing message
        response = client.post("/api/chat", json={
            "user_id": "test_user"
        })
        assert response.status_code == 422
        
        # Test empty message
        response = client.post("/api/chat", json={
            "user_id": "test_user",
            "message": ""
        })
        assert response.status_code == 422
    
    def test_session_isolation(self, test_client):
        """Test that different sessions are properly isolated."""
        client, memory_service = test_client
        
        # Add memory to different sessions
        asyncio.run(memory_service.add_exchange("test_user", "Workout question", "Workout answer", "workout"))
        asyncio.run(memory_service.add_exchange("test_user", "Nutrition question", "Nutrition answer", "nutrition"))
        
        # Get conversation history for each session
        workout_response = client.get("/api/memory/conversation/test_user?session_id=workout")
        nutrition_response = client.get("/api/memory/conversation/test_user?session_id=nutrition")
        
        assert workout_response.status_code == 200
        assert nutrition_response.status_code == 200
        
        workout_data = workout_response.json()
        nutrition_data = nutrition_response.json()
        
        assert workout_data["session_id"] == "workout"
        assert nutrition_data["session_id"] == "nutrition"
        
        # Check that sessions contain different content
        workout_content = " ".join([msg["content"] for msg in workout_data["messages"]])
        nutrition_content = " ".join([msg["content"] for msg in nutrition_data["messages"]])
        
        assert "Workout" in workout_content
        assert "Nutrition" in nutrition_content
        assert "Nutrition" not in workout_content
        assert "Workout" not in nutrition_content
    
    def test_large_conversation_handling(self, test_client):
        """Test handling of large conversations."""
        client, memory_service = test_client
        
        # Add many messages
        for i in range(25):  # 25 exchanges = 50 messages
            asyncio.run(memory_service.add_exchange("test_user", f"Message {i}", f"Response {i}"))
        
        # Get conversation history with limit
        response = client.get("/api/memory/conversation/test_user?limit=20")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message_count"] <= 20
        assert len(data["messages"]) <= 20
        
        # Get stats
        stats_response = client.get("/api/memory/stats/test_user")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["message_count"] == 50


# Test configuration for pytest
if __name__ == "__main__":
    pytest.main([__file__]) 