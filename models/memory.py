from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum

class MessageRole(str, Enum):
    """Enum for message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class ConversationMessage(BaseModel):
    """Individual message in a conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    agent_name: Optional[str] = None

class ConversationHistory(BaseModel):
    """Complete conversation history for a user."""
    user_id: str
    session_id: str = Field(default="default")
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}

class MemoryConfiguration(BaseModel):
    """Configuration for memory management."""
    max_messages_per_user: int = 100
    max_characters_per_message: int = 2000
    memory_cleanup_interval_hours: int = 24
    max_conversation_age_days: int = 30
    enable_memory_compression: bool = True
    memory_storage_backend: str = "file"  # "memory", "file", "database"

class MemoryStats(BaseModel):
    """Statistics about memory usage."""
    total_users: int
    total_conversations: int
    total_messages: int
    memory_size_mb: float
    oldest_conversation: Optional[datetime] = None
    newest_conversation: Optional[datetime] = None

class MemorySearchQuery(BaseModel):
    """Query for searching conversation history."""
    user_id: str
    query: str
    max_results: int = 10
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_content: bool = True

class MemorySearchResult(BaseModel):
    """Result from memory search."""
    user_id: str
    session_id: str
    message: ConversationMessage
    relevance_score: float
    context_messages: List[ConversationMessage] = Field(default_factory=list) 