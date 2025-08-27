"""LangSmith tracing service for Pili fitness chatbot.

This module provides centralized LangSmith tracing configuration and utilities.
"""

import os
import logging
from typing import Optional, Dict, Any
from config.settings import get_configuration

logger = logging.getLogger(__name__)


class TracingService:
    """Service for managing LangSmith tracing configuration."""
    
    def __init__(self):
        self.initialized = False
        self.config = get_configuration()
    
    def initialize_tracing(self) -> bool:
        """Initialize LangSmith tracing using default environment variables."""
        try:
            # Check if LangSmith is configured via environment variables
            langchain_api_key = os.environ.get('LANGCHAIN_API_KEY')
            langchain_tracing = os.environ.get('LANGCHAIN_TRACING_V2', 'false').lower()
            
            if not langchain_api_key:
                logger.info("LangSmith tracing disabled: No LANGCHAIN_API_KEY environment variable set")
                self._disable_tracing()
                return False
            
            # LangSmith will automatically use environment variables:
            # - LANGCHAIN_API_KEY: API key for authentication
            # - LANGCHAIN_TRACING_V2: Enable/disable tracing (default: false)
            # - LANGCHAIN_PROJECT: Project name (optional)
            # - LANGCHAIN_ENDPOINT: API endpoint (optional, defaults to https://api.smith.langchain.com)
            
            # Enable tracing if not already enabled
            if langchain_tracing != 'true':
                os.environ['LANGCHAIN_TRACING_V2'] = 'true'
                logger.info("Enabled LANGCHAIN_TRACING_V2")
            
            # Import and test LangSmith connection
            from langsmith import Client
            
            # Client will automatically use environment variables
            client = Client()
            
            # Verify connection by trying to list projects
            try:
                projects = list(client.list_projects(limit=1))
                project_name = os.environ.get('LANGCHAIN_PROJECT', 'default')
                logger.info(f"✅ LangSmith tracing initialized for project: {project_name}")
                self.initialized = True
                return True
            except Exception as e:
                logger.warning(f"LangSmith connection test failed: {e}")
                self._disable_tracing()
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith tracing: {e}")
            self._disable_tracing()
            return False
    
    def _disable_tracing(self):
        """Disable LangSmith tracing."""
        os.environ['LANGCHAIN_TRACING_V2'] = 'false'
        self.initialized = False
        logger.info("🔕 LangSmith tracing disabled")
    
    def is_enabled(self) -> bool:
        """Check if tracing is enabled and working."""
        return self.initialized and os.environ.get('LANGCHAIN_TRACING_V2') == 'true'
    
    def get_tracing_metadata(self) -> Dict[str, Any]:
        """Get metadata about current tracing configuration."""
        return {
            "tracing_enabled": self.is_enabled(),
            "project": os.environ.get('LANGCHAIN_PROJECT') if self.is_enabled() else None,
            "endpoint": os.environ.get('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com') if self.is_enabled() else None,
            "api_key_configured": bool(os.environ.get('LANGCHAIN_API_KEY'))
        }
    
    def create_run_metadata(self, user_id: str, operation: str, **kwargs) -> Dict[str, Any]:
        """Create standardized metadata for LangSmith runs."""
        base_metadata = {
            "user_id": user_id,
            "operation": operation,
            "service": "pili_fitness_chatbot",
            "version": "1.0.0"
        }
        base_metadata.update(kwargs)
        return base_metadata


# Global tracing service instance
tracing_service = TracingService()


def initialize_tracing() -> bool:
    """Initialize tracing service."""
    return tracing_service.initialize_tracing()


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled."""
    return tracing_service.is_enabled()


def get_tracing_metadata() -> Dict[str, Any]:
    """Get tracing metadata."""
    return tracing_service.get_tracing_metadata()


def create_run_metadata(user_id: str, operation: str, **kwargs) -> Dict[str, Any]:
    """Create run metadata."""
    return tracing_service.create_run_metadata(user_id, operation, **kwargs)

