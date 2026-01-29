"""
Error Handler Middleware for global exception handling.

Catches unhandled exceptions and converts them to
structured error responses.
"""

import traceback
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.utils.logging import get_logger
from app.utils.exceptions import MarketPulseError

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware.
    
    Catches all unhandled exceptions and returns
    structured JSON error responses.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ):
        try:
            response = await call_next(request)
            return response

        except MarketPulseError as e:
            # Handle custom exceptions
            logger.error(
                "market_pulse_error",
                code=e.code,
                message=e.message,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": e.code,
                    "message": e.message,
                    "details": e.details,
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        except Exception as e:
            # Handle unexpected exceptions
            logger.error(
                "unhandled_exception",
                error=str(e),
                error_type=type(e).__name__,
                path=request.url.path,
                traceback=traceback.format_exc(),
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
