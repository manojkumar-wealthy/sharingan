"""
OpenTelemetry distributed tracing setup for Market Pulse Multi-Agent API.

Provides end-to-end tracing across agent executions for:
- Performance monitoring
- Error tracking
- Request flow visualization
"""

from contextlib import contextmanager
from typing import Optional, Generator, Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Span, Status, StatusCode

from app.config import get_settings


# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def setup_tracing() -> None:
    """
    Initialize OpenTelemetry tracing.
    
    Sets up the tracer provider with appropriate exporters based on configuration.
    In production, this would use Cloud Trace or another backend.
    """
    global _tracer
    settings = get_settings()

    if not settings.ENABLE_TRACING:
        return

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": "market-pulse-api",
            "service.version": "2.0.0",
            "deployment.environment": "development",
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add console exporter for development
    # In production, replace with Cloud Trace exporter:
    # from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    # cloud_trace_exporter = CloudTraceSpanExporter(
    #     project_id=settings.VERTEX_AI_PROJECT_ID
    # )
    # provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))

    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Create tracer instance
    _tracer = trace.get_tracer(__name__)


def get_tracer() -> trace.Tracer:
    """
    Get the global tracer instance.
    
    Returns:
        OpenTelemetry Tracer instance.
    """
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(__name__)
    return _tracer


@contextmanager
def trace_agent_execution(
    agent_name: str,
    request_id: str,
    user_id: Optional[str] = None,
    **attributes: Any,
) -> Generator[Span, None, None]:
    """
    Context manager for tracing agent execution.
    
    Args:
        agent_name: Name of the agent being executed
        request_id: Request ID for correlation
        user_id: Optional user ID
        **attributes: Additional span attributes
    
    Yields:
        The active span for the agent execution.
    
    Example:
        with trace_agent_execution("market_data_agent", request_id) as span:
            result = await agent.execute(input_data)
            span.set_attribute("result_status", "success")
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(
        f"{agent_name}_execution",
        kind=trace.SpanKind.INTERNAL,
    ) as span:
        # Set standard attributes
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("request.id", request_id)
        if user_id:
            span.set_attribute("user.id", user_id)

        # Set custom attributes
        for key, value in attributes.items():
            span.set_attribute(key, value)

        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


@contextmanager
def trace_tool_execution(
    tool_name: str,
    **attributes: Any,
) -> Generator[Span, None, None]:
    """
    Context manager for tracing tool execution within an agent.
    
    Args:
        tool_name: Name of the tool being executed
        **attributes: Additional span attributes
    
    Yields:
        The active span for the tool execution.
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(
        f"tool_{tool_name}",
        kind=trace.SpanKind.INTERNAL,
    ) as span:
        span.set_attribute("tool.name", tool_name)

        for key, value in attributes.items():
            span.set_attribute(key, value)

        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


@contextmanager
def trace_orchestration(
    request_id: str,
    user_id: str,
    **attributes: Any,
) -> Generator[Span, None, None]:
    """
    Context manager for tracing the full orchestration.
    
    This creates the root span for the entire market pulse generation.
    
    Args:
        request_id: Request ID for correlation
        user_id: User ID making the request
        **attributes: Additional span attributes
    
    Yields:
        The root span for the orchestration.
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(
        "market_pulse_orchestration",
        kind=trace.SpanKind.SERVER,
    ) as span:
        span.set_attribute("request.id", request_id)
        span.set_attribute("user.id", user_id)

        for key, value in attributes.items():
            span.set_attribute(key, value)

        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def add_span_event(name: str, attributes: Optional[dict] = None) -> None:
    """
    Add an event to the current span.
    
    Args:
        name: Event name
        attributes: Optional event attributes
    """
    span = trace.get_current_span()
    span.add_event(name, attributes=attributes or {})


def set_span_status(success: bool, message: Optional[str] = None) -> None:
    """
    Set the status of the current span.
    
    Args:
        success: Whether the operation succeeded
        message: Optional status message
    """
    span = trace.get_current_span()
    if success:
        span.set_status(Status(StatusCode.OK, message))
    else:
        span.set_status(Status(StatusCode.ERROR, message))
