"""
Error Handling Middleware for Project AEGIS
FastAPI middleware for centralized error processing and response formatting
"""

import time
import uuid
import logging
from typing import Callable
from datetime import datetime

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .error_handler import (
    ErrorHandler,
    ErrorContext,
    ErrorSeverity,
    AEGISException,
    create_error_response
)

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling errors in FastAPI requests
    Provides centralized error processing, logging, and response formatting
    """

    def __init__(self, app: ASGIApp, error_handler: ErrorHandler = None):
        super().__init__(app)
        self.error_handler = error_handler or ErrorHandler()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any errors"""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Create error context
        context = ErrorContext(
            request_id=request_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            endpoint=request.url.path,
            method=request.method,
            timestamp=datetime.utcnow(),
            environment=request.app.state.get("environment", "unknown")
        )

        # Add request ID to response headers
        response = Response()

        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Add timing and request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"

            return response

        except HTTPException as http_exception:
            # Handle HTTP exceptions (FastAPI validation, etc.)
            context.user_id = getattr(request.state, "user_id", None)
            context.session_id = getattr(request.state, "session_id", None)

            error_detail = self.error_handler.create_error_detail(http_exception, context)

            # Log HTTP exception
            logger.warning(
                f"HTTP Exception: {http_exception.status_code} - {http_exception.detail}",
                extra={
                    "request_id": request_id,
                    "endpoint": context.endpoint,
                    "method": context.method,
                    "status_code": http_exception.status_code
                }
            )

            return create_error_response(error_detail)

        except AEGISException as aegis_exception:
            # Handle custom AEGIS exceptions
            context.user_id = getattr(request.state, "user_id", None)
            context.session_id = getattr(request.state, "session_id", None)

            error_detail = self.error_handler.handle_exception(aegis_exception, context)

            return create_error_response(error_detail)

        except Exception as exception:
            # Handle unexpected exceptions
            context.user_id = getattr(request.state, "user_id", None)
            context.session_id = getattr(request.state, "session_id", None)

            error_detail = self.error_handler.handle_exception(exception, context)

            # For critical errors, add additional context
            if error_detail.severity == ErrorSeverity.CRITICAL:
                logger.critical(
                    f"Critical error in request {request_id}: {exception}",
                    extra={
                        "request_id": request_id,
                        "endpoint": context.endpoint,
                        "method": context.method,
                        "traceback": error_detail.stack_trace
                    },
                    exc_info=True
                )

            return create_error_response(error_detail)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request information"""

    def __init__(self, app: ASGIApp, logger_name: str = "request"):
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response information"""
        start_time = time.time()
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        # Log request
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "content_type": request.headers.get("content-type"),
                "content_length": request.headers.get("content-length")
            }
        )

        try:
            response = await call_next(request)

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000

            # Log response
            self.logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "processing_time_ms": processing_time,
                    "response_size": response.headers.get("content-length"),
                    "content_type": response.headers.get("content-type")
                }
            )

            # Add processing time to response header
            response.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"

            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            # Log error
            self.logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "processing_time_ms": processing_time,
                    "error": str(e)
                },
                exc_info=True
            )

            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        # Remove potentially sensitive headers
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)

        return response

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware (for demonstration)"""

    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Implement basic rate limiting"""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        minute_window = int(current_time // 60) * 60

        # Clean old entries
        cutoff_time = current_time - 300  # 5 minutes
        self.request_counts = {
            ip: counts for ip, counts in self.request_counts.items()
            if any(timestamp > cutoff_time for timestamp in counts.keys())
        }

        # Check rate limit
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}

        # Count requests in current minute
        current_minute_count = sum(
            1 for timestamp in self.request_counts[client_ip].keys()
            if timestamp >= minute_window
        )

        if current_minute_count >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        # Record this request
        self.request_counts[client_ip][current_time] = True

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - current_minute_count - 1)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(minute_window + 60))

        return response

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Circuit breaker middleware for protecting against cascading failures"""

    def __init__(self, app: ASGIApp, error_handler: ErrorHandler = None):
        super().__init__(app)
        self.error_handler = error_handler or ErrorHandler()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Implement circuit breaker pattern"""
        # Extract service name from endpoint
        service = self._extract_service_from_endpoint(request.url.path)

        # Check if circuit is open
        if self.error_handler.is_circuit_open(service):
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "Service temporarily unavailable",
                    "error_code": "CIRCUIT_BREAKER_OPEN",
                    "service": service,
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        try:
            response = await call_next(request)

            # Record success for circuit breaker
            if response.status_code < 500:
                self.error_handler.record_success(service)

            return response

        except Exception as e:
            # Error will be handled by ErrorHandlingMiddleware
            # Circuit breaker state will be updated there
            raise

    def _extract_service_from_endpoint(self, path: str) -> str:
        """Extract service name from endpoint path"""
        if '/auth' in path:
            return 'auth_service'
        elif '/complaints' in path:
            return 'complaint_service'
        elif '/predictions' in path:
            return 'prediction_service'
        elif '/cordons' in path:
            return 'cordon_service'
        elif '/alerts' in path:
            return 'alert_service'
        elif '/analytics' in path:
            return 'analytics_service'
        elif '/users' in path:
            return 'user_service'
        elif '/system' in path:
            return 'system_service'
        else:
            return 'unknown_service'

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health check endpoints"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.health_check_paths = ["/health", "/healthz", "/ping"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Bypass error handling for health check endpoints"""
        if request.url.path in self.health_check_paths:
            # Handle health check directly
            try:
                # Simple health check
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "healthy",
                        "timestamp": datetime.utcnow().isoformat(),
                        "service": "Project AEGIS"
                    }
                )
            except Exception as e:
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "unhealthy",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": str(e)
                    }
                )

        return await call_next(request)

# Middleware factory functions
def add_error_handling_middleware(app, error_handler: ErrorHandler = None):
    """Add error handling middleware to FastAPI app"""
    app.add_middleware(ErrorHandlingMiddleware, error_handler=error_handler)

def add_logging_middleware(app):
    """Add request logging middleware to FastAPI app"""
    app.add_middleware(RequestLoggingMiddleware)

def add_security_middleware(app):
    """Add security headers middleware to FastAPI app"""
    app.add_middleware(SecurityHeadersMiddleware)

def add_rate_limiting_middleware(app, requests_per_minute: int = 60):
    """Add rate limiting middleware to FastAPI app"""
    app.add_middleware(RateLimitingMiddleware, requests_per_minute=requests_per_minute)

def add_circuit_breaker_middleware(app, error_handler: ErrorHandler = None):
    """Add circuit breaker middleware to FastAPI app"""
    app.add_middleware(CircuitBreakerMiddleware, error_handler=error_handler)

def add_health_check_middleware(app):
    """Add health check middleware to FastAPI app"""
    app.add_middleware(HealthCheckMiddleware)

def add_all_middleware(app, error_handler: ErrorHandler = None, requests_per_minute: int = 60):
    """Add all middleware to FastAPI app in the correct order"""
    # Order matters - first applied = outermost

    # Health check (bypass other middleware)
    add_health_check_middleware(app)

    # Security headers
    add_security_middleware(app)

    # Rate limiting
    add_rate_limiting_middleware(app, requests_per_minute)

    # Circuit breaker
    add_circuit_breaker_middleware(app, error_handler)

    # Request logging
    add_logging_middleware(app)

    # Error handling (should be innermost)
    add_error_handling_middleware(app, error_handler)

# Middleware configuration
DEFAULT_MIDDLEWARE_CONFIG = {
    "error_handling": True,
    "logging": True,
    "security_headers": True,
    "rate_limiting": True,
    "rate_limit_per_minute": 60,
    "circuit_breaker": True,
    "health_check": True
}

def configure_middleware(app, config: dict = None, error_handler: ErrorHandler = None):
    """Configure middleware based on configuration"""
    config = {**DEFAULT_MIDDLEWARE_CONFIG, **(config or {})}

    if config.get("health_check", True):
        add_health_check_middleware(app)

    if config.get("security_headers", True):
        add_security_middleware(app)

    if config.get("rate_limiting", True):
        add_rate_limiting_middleware(app, config.get("rate_limit_per_minute", 60))

    if config.get("circuit_breaker", True):
        add_circuit_breaker_middleware(app, error_handler)

    if config.get("logging", True):
        add_logging_middleware(app)

    if config.get("error_handling", True):
        add_error_handling_middleware(app, error_handler)

    logger.info("Middleware configured successfully")

# Export components
__all__ = [
    'ErrorHandlingMiddleware',
    'RequestLoggingMiddleware',
    'SecurityHeadersMiddleware',
    'RateLimitingMiddleware',
    'CircuitBreakerMiddleware',
    'HealthCheckMiddleware',
    'add_error_handling_middleware',
    'add_logging_middleware',
    'add_security_middleware',
    'add_rate_limiting_middleware',
    'add_circuit_breaker_middleware',
    'add_health_check_middleware',
    'add_all_middleware',
    'configure_middleware',
    'DEFAULT_MIDDLEWARE_CONFIG'
]