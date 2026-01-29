"""
Request ID Middleware for request tracing.

Adds a unique request ID to each incoming request
for distributed tracing and logging correlation.
"""

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logging import bind_request_context


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to all requests.
    
    - Adds X-Request-ID header to requests if not present
    - Binds request context for logging
    - Adds X-Request-ID to response headers
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Get user ID if present (from auth or header)
        user_id = request.headers.get("X-User-ID")

        # Bind context for logging
        bind_request_context(request_id, user_id)

        # Store in request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
