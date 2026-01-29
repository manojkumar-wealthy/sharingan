"""
Utility modules for Market Pulse Multi-Agent API.

Contains:
- logging: Structured logging setup
- exceptions: Custom exception classes
- tracing: OpenTelemetry distributed tracing
- vertex_ai_client: Vertex AI client wrapper
"""

from app.utils.exceptions import (
    MarketPulseError,
    AgentExecutionError,
    AgentTimeoutError,
    AgentReasoningError,
    DataValidationError,
    DataFetchError,
    OrchestrationError,
)
from app.utils.logging import setup_logging, get_logger

__all__ = [
    # Exceptions
    "MarketPulseError",
    "AgentExecutionError",
    "AgentTimeoutError",
    "AgentReasoningError",
    "DataValidationError",
    "DataFetchError",
    "OrchestrationError",
    # Logging
    "setup_logging",
    "get_logger",
]
