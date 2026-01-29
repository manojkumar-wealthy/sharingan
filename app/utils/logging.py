"""
Structured logging setup for Market Pulse Multi-Agent API.

Uses structlog for structured, JSON-friendly logging with:
- Request ID tracking
- Agent-specific context
- Performance metrics
"""

import logging
import sys
from typing import Optional

import structlog
from structlog.types import Processor

from app.config import get_settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Optional log level override. Defaults to settings.LOG_LEVEL.
    """
    settings = get_settings()
    level = log_level or settings.LOG_LEVEL

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Define shared processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure formatter for stdlib handler
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    # Apply formatter to root handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper()))


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Optional logger name. Defaults to the calling module.
    
    Returns:
        A structlog BoundLogger instance.
    """
    return structlog.get_logger(name)


def bind_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """
    Bind request context to all subsequent log messages.
    
    Args:
        request_id: Unique request identifier
        user_id: Optional user identifier
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        user_id=user_id,
    )


def bind_agent_context(agent_name: str, **kwargs) -> None:
    """
    Bind agent-specific context to log messages.
    
    Args:
        agent_name: Name of the agent
        **kwargs: Additional context to bind
    """
    structlog.contextvars.bind_contextvars(
        agent=agent_name,
        **kwargs,
    )


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


class AgentLogger:
    """
    Convenience logger wrapper for agents.
    
    Provides pre-bound context for agent-specific logging.
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._logger = get_logger(agent_name)

    def _log(self, level: str, event: str, **kwargs):
        """Internal log method with agent context."""
        log_method = getattr(self._logger, level)
        log_method(event, agent=self.agent_name, **kwargs)

    def info(self, event: str, **kwargs):
        """Log info level message."""
        self._log("info", event, **kwargs)

    def debug(self, event: str, **kwargs):
        """Log debug level message."""
        self._log("debug", event, **kwargs)

    def warning(self, event: str, **kwargs):
        """Log warning level message."""
        self._log("warning", event, **kwargs)

    def error(self, event: str, **kwargs):
        """Log error level message."""
        self._log("error", event, **kwargs)

    def execution_start(self, request_id: str, **kwargs):
        """Log agent execution start."""
        self.info(
            "agent_execution_start",
            request_id=request_id,
            **kwargs,
        )

    def execution_success(self, request_id: str, execution_time_ms: int, **kwargs):
        """Log agent execution success."""
        self.info(
            "agent_execution_success",
            request_id=request_id,
            execution_time_ms=execution_time_ms,
            **kwargs,
        )

    def execution_failure(self, request_id: str, error: str, **kwargs):
        """Log agent execution failure."""
        self.error(
            "agent_execution_failure",
            request_id=request_id,
            error=error,
            **kwargs,
        )

    def tool_called(self, tool_name: str, **kwargs):
        """Log tool invocation."""
        self.info(
            "tool_called",
            tool_name=tool_name,
            **kwargs,
        )

    def tool_result(self, tool_name: str, success: bool, **kwargs):
        """Log tool result."""
        self.info(
            "tool_result",
            tool_name=tool_name,
            success=success,
            **kwargs,
        )
