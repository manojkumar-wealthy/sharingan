"""
Middleware for Market Pulse Multi-Agent API.

Contains:
- error_handler: Global error handling middleware
- request_id: Request ID injection middleware
"""

from app.middleware.request_id import RequestIDMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware

__all__ = [
    "RequestIDMiddleware",
    "ErrorHandlerMiddleware",
]
