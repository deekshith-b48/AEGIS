"""
Comprehensive Error Handler for Project AEGIS
Centralized error handling, logging, and recovery mechanisms
"""

import os
import sys
import traceback
import logging
import asyncio
import functools
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from redis.exceptions import RedisError
import jwt

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    AI_MODEL = "ai_model"
    SYSTEM = "system"
    NETWORK = "network"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Error context information"""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    timestamp: datetime = None
    environment: str = "unknown"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class ErrorDetail:
    """Detailed error information"""
    error_id: str
    error_type: str
    error_code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    stack_trace: Optional[str] = None
    cause: Optional[str] = None
    recoverable: bool = False
    retry_after: Optional[int] = None
    suggestions: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.metadata is None:
            self.metadata = {}

class AEGISException(Exception):
    """Base exception for Project AEGIS"""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: ErrorContext = None,
        recoverable: bool = False,
        retry_after: Optional[int] = None,
        suggestions: List[str] = None,
        metadata: Dict[str, Any] = None,
        cause: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.suggestions = suggestions or []
        self.metadata = metadata or {}
        self.cause = cause
        self.error_id = f"ERR_{int(datetime.utcnow().timestamp() * 1000)}"

class ValidationError(AEGISException):
    """Validation error"""

    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            **kwargs
        )
        if field:
            self.metadata["field"] = field
        if value is not None:
            self.metadata["value"] = str(value)

class AuthenticationError(AEGISException):
    """Authentication error"""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            **kwargs
        )

class AuthorizationError(AEGISException):
    """Authorization error"""

    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            **kwargs
        )

class DatabaseError(AEGISException):
    """Database error"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_after=5,
            **kwargs
        )

class CacheError(AEGISException):
    """Cache error"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            category=ErrorCategory.CACHE,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_after=2,
            **kwargs
        )

class ExternalAPIError(AEGISException):
    """External API error"""

    def __init__(self, message: str, service: str = None, status_code: int = None, **kwargs):
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_after=10,
            **kwargs
        )
        if service:
            self.metadata["service"] = service
        if status_code:
            self.metadata["status_code"] = status_code

class AIModelError(AEGISException):
    """AI model error"""

    def __init__(self, message: str, model_name: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code="AI_MODEL_ERROR",
            category=ErrorCategory.AI_MODEL,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_after=5,
            **kwargs
        )
        if model_name:
            self.metadata["model_name"] = model_name

class SystemError(AEGISException):
    """System error"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="SYSTEM_ERROR",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            recoverable=False,
            **kwargs
        )

class NetworkError(AEGISException):
    """Network error"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_after=15,
            **kwargs
        )

class BusinessLogicError(AEGISException):
    """Business logic error"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.LOW,
            recoverable=False,
            **kwargs
        )

class ErrorHandler:
    """
    Comprehensive error handling system
    Provides centralized error processing, logging, and recovery mechanisms
    """

    def __init__(self):
        self.error_history: List[ErrorDetail] = []
        self.error_stats: Dict[str, int] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self._initialize_circuit_breakers()

    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for external services"""
        services = [
            'database', 'redis', 'kafka', 'npci_api', 'ncrp_api',
            'i4c_api', 'cfcfrms_api', 'ai_models'
        ]

        for service in services:
            self.circuit_breakers[service] = {
                'state': 'closed',  # closed, open, half_open
                'failure_count': 0,
                'last_failure_time': None,
                'success_threshold': 5,
                'failure_threshold': 5,
                'recovery_timeout': 60,  # seconds
                'retry_count': 0,
                'max_retries': 3
            }

    def create_error_detail(self, exception: Exception, context: ErrorContext = None) -> ErrorDetail:
        """Create detailed error information from exception"""
        if isinstance(exception, AEGISException):
            return ErrorDetail(
                error_id=exception.error_id,
                error_type=exception.__class__.__name__,
                error_code=exception.error_code,
                message=exception.message,
                category=exception.category,
                severity=exception.severity,
                context=context or exception.context,
                stack_trace=traceback.format_exc(),
                cause=str(exception.cause) if exception.cause else None,
                recoverable=exception.recoverable,
                retry_after=exception.retry_after,
                suggestions=exception.suggestions,
                metadata=exception.metadata
            )

        # Handle standard exceptions
        error_type = exception.__class__.__name__
        error_code = error_type.upper()

        if isinstance(exception, HTTPException):
            category = ErrorCategory.BUSINESS_LOGIC
            severity = ErrorSeverity.LOW
            message = exception.detail
        elif isinstance(exception, (SQLAlchemyError, IntegrityError, OperationalError)):
            category = ErrorCategory.DATABASE
            severity = ErrorSeverity.HIGH
            message = "Database operation failed"
        elif isinstance(exception, (RedisError, ConnectionError)):
            category = ErrorCategory.CACHE if 'redis' in str(type(exception)).lower() else ErrorCategory.NETWORK
            severity = ErrorSeverity.MEDIUM
            message = "Cache/Network operation failed"
        elif isinstance(exception, jwt.InvalidTokenError):
            category = ErrorCategory.AUTHENTICATION
            severity = ErrorSeverity.HIGH
            message = "Invalid authentication token"
        elif isinstance(exception, (ValueError, TypeError)):
            category = ErrorCategory.VALIDATION
            severity = ErrorSeverity.LOW
            message = "Invalid input data"
        else:
            category = ErrorCategory.UNKNOWN
            severity = ErrorSeverity.MEDIUM
            message = str(exception)

        return ErrorDetail(
            error_id=f"ERR_{int(datetime.utcnow().timestamp() * 1000)}",
            error_type=error_type,
            error_code=error_code,
            message=message,
            category=category,
            severity=severity,
            context=context or ErrorContext(),
            stack_trace=traceback.format_exc(),
            recoverable=category in [ErrorCategory.DATABASE, ErrorCategory.CACHE, ErrorCategory.EXTERNAL_API],
            retry_after=self._get_default_retry_after(category),
            suggestions=self._get_default_suggestions(category)
        )

    def _get_default_retry_after(self, category: ErrorCategory) -> Optional[int]:
        """Get default retry delay for error category"""
        retry_map = {
            ErrorCategory.DATABASE: 5,
            ErrorCategory.CACHE: 2,
            ErrorCategory.EXTERNAL_API: 10,
            ErrorCategory.NETWORK: 15,
            ErrorCategory.AI_MODEL: 5
        }
        return retry_map.get(category)

    def _get_default_suggestions(self, category: ErrorCategory) -> List[str]:
        """Get default suggestions for error category"""
        suggestions_map = {
            ErrorCategory.VALIDATION: [
                "Check input parameters",
                "Verify data format and types",
                "Ensure all required fields are provided"
            ],
            ErrorCategory.AUTHENTICATION: [
                "Check your credentials",
                "Ensure token is valid and not expired",
                "Try logging out and logging back in"
            ],
            ErrorCategory.AUTHORIZATION: [
                "Check if you have the required permissions",
                "Contact administrator for access",
                "Verify your user role and privileges"
            ],
            ErrorCategory.DATABASE: [
                "Try again in a few moments",
                "Contact support if issue persists",
                "Check database connectivity"
            ],
            ErrorCategory.CACHE: [
                "Cache service temporarily unavailable",
                "Try again in a moment",
                "Some features may be limited"
            ],
            ErrorCategory.EXTERNAL_API: [
                "External service temporarily unavailable",
                "Try again in a few moments",
                "Contact support if issue persists"
            ],
            ErrorCategory.AI_MODEL: [
                "AI service temporarily unavailable",
                "Try again in a moment",
                "Some predictions may be unavailable"
            ],
            ErrorCategory.SYSTEM: [
                "System temporarily unavailable",
                "Contact support immediately",
                "Try again later"
            ],
            ErrorCategory.NETWORK: [
                "Check your internet connection",
                "Try again in a moment",
                "Contact support if issue persists"
            ]
        }
        return suggestions_map.get(category, ["Contact support for assistance"])

    def handle_exception(self, exception: Exception, context: ErrorContext = None) -> ErrorDetail:
        """Handle exception and create error detail"""
        error_detail = self.create_error_detail(exception, context)

        # Add to error history
        self.error_history.append(error_detail)

        # Update statistics
        error_key = f"{error_detail.category.value}_{error_detail.error_code}"
        self.error_stats[error_key] = self.error_stats.get(error_key, 0) + 1

        # Log error
        self._log_error(error_detail)

        # Check circuit breaker
        if context and context.endpoint:
            service = self._extract_service_from_endpoint(context.endpoint)
            self._update_circuit_breaker(service, error_detail)

        # Attempt recovery if possible
        if error_detail.recoverable:
            self._attempt_recovery(error_detail)

        return error_detail

    def _log_error(self, error_detail: ErrorDetail):
        """Log error with appropriate level"""
        log_data = {
            'error_id': error_detail.error_id,
            'error_type': error_detail.error_type,
            'error_code': error_detail.error_code,
            'message': error_detail.message,
            'category': error_detail.category.value,
            'severity': error_detail.severity.value,
            'context': asdict(error_detail.context),
            'recoverable': error_detail.recoverable,
            'metadata': error_detail.metadata
        }

        if error_detail.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {error_detail.message}", extra=log_data)
        elif error_detail.severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR: {error_detail.message}", extra=log_data)
        elif error_detail.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR: {error_detail.message}", extra=log_data)
        else:
            logger.info(f"LOW SEVERITY ERROR: {error_detail.message}", extra=log_data)

    def _extract_service_from_endpoint(self, endpoint: str) -> str:
        """Extract service name from endpoint"""
        if '/api/v1/auth' in endpoint:
            return 'auth_service'
        elif '/api/v1/complaints' in endpoint:
            return 'complaint_service'
        elif '/api/v1/predictions' in endpoint:
            return 'prediction_service'
        elif '/api/v1/cordons' in endpoint:
            return 'cordon_service'
        elif '/api/v1/alerts' in endpoint:
            return 'alert_service'
        elif '/api/v2/analytics' in endpoint:
            return 'analytics_service'
        else:
            return 'unknown_service'

    def _update_circuit_breaker(self, service: str, error_detail: ErrorDetail):
        """Update circuit breaker state based on error"""
        if service not in self.circuit_breakers:
            return

        breaker = self.circuit_breakers[service]

        # Update failure count for errors
        if error_detail.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            breaker['failure_count'] += 1
            breaker['last_failure_time'] = datetime.utcnow()

        # Check if circuit should be opened
        if (breaker['state'] == 'closed' and
            breaker['failure_count'] >= breaker['failure_threshold']):
            breaker['state'] = 'open'
            logger.warning(f"Circuit breaker opened for service: {service}")

        # Check if circuit should be half-open (recovery timeout)
        elif (breaker['state'] == 'open' and
              breaker['last_failure_time'] and
              (datetime.utcnow() - breaker['last_failure_time']).total_seconds() > breaker['recovery_timeout']):
            breaker['state'] = 'half_open'
            breaker['retry_count'] = 0
            logger.info(f"Circuit breaker half-open for service: {service}")

    def _attempt_recovery(self, error_detail: ErrorDetail):
        """Attempt to recover from error"""
        recovery_key = f"{error_detail.category.value}_{error_detail.error_code}"

        if recovery_key in self.recovery_strategies:
            try:
                self.recovery_strategies[recovery_key](error_detail)
                logger.info(f"Recovery attempted for error: {error_detail.error_id}")
            except Exception as recovery_error:
                logger.error(f"Recovery failed for error {error_detail.error_id}: {recovery_error}")

    def register_recovery_strategy(self, error_pattern: str, strategy: Callable):
        """Register recovery strategy for error pattern"""
        self.recovery_strategies[error_pattern] = strategy
        logger.info(f"Recovery strategy registered for pattern: {error_pattern}")

    def is_circuit_open(self, service: str) -> bool:
        """Check if circuit breaker is open for service"""
        if service not in self.circuit_breakers:
            return False

        return self.circuit_breakers[service]['state'] == 'open'

    def record_success(self, service: str):
        """Record successful operation for circuit breaker"""
        if service not in self.circuit_breakers:
            return

        breaker = self.circuit_breakers[service]

        if breaker['state'] == 'half_open':
            breaker['retry_count'] += 1
            if breaker['retry_count'] >= breaker['success_threshold']:
                breaker['state'] = 'closed'
                breaker['failure_count'] = 0
                logger.info(f"Circuit breaker closed for service: {service}")

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        total_errors = sum(self.error_stats.values())
        category_stats = {}

        for key, count in self.error_stats.items():
            category = key.split('_')[0]
            category_stats[category] = category_stats.get(category, 0) + count

        recent_errors = [
            error for error in self.error_history
            if (datetime.utcnow() - error.context.timestamp).total_seconds() < 3600  # Last hour
        ]

        return {
            'total_errors': total_errors,
            'errors_by_category': category_stats,
            'errors_by_type': dict(self.error_stats),
            'recent_errors_count': len(recent_errors),
            'circuit_breakers': {
                service: {
                    'state': breaker['state'],
                    'failure_count': breaker['failure_count']
                }
                for service, breaker in self.circuit_breakers.items()
            },
            'generated_at': datetime.utcnow().isoformat()
        }

    def get_error_history(self, hours: int = 24, severity: ErrorSeverity = None) -> List[Dict[str, Any]]:
        """Get error history for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        filtered_errors = [
            error for error in self.error_history
            if error.context.timestamp >= cutoff_time
        ]

        if severity:
            filtered_errors = [
                error for error in filtered_errors
                if error.severity == severity
            ]

        return [asdict(error) for error in filtered_errors[-100:]]  # Last 100 errors

# Global error handler instance
error_handler = ErrorHandler()

# FastAPI error handling middleware
def create_error_response(error_detail: ErrorDetail) -> JSONResponse:
    """Create standardized error response"""
    response_data = {
        "success": False,
        "error": error_detail.message,
        "error_code": error_detail.error_code,
        "error_id": error_detail.error_id,
        "category": error_detail.category.value,
        "severity": error_detail.severity.value,
        "recoverable": error_detail.recoverable,
        "retry_after": error_detail.retry_after,
        "suggestions": error_detail.suggestions,
        "timestamp": error_detail.context.timestamp.isoformat()
    }

    # Add metadata in development mode
    if os.getenv("ENVIRONMENT", "development") == "development":
        response_data["debug"] = {
            "error_type": error_detail.error_type,
            "stack_trace": error_detail.stack_trace,
            "context": asdict(error_detail.context),
            "metadata": error_detail.metadata
        }

    # Set appropriate HTTP status code
    status_code = _get_http_status_code(error_detail)

    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

def _get_http_status_code(error_detail: ErrorDetail) -> int:
    """Get appropriate HTTP status code for error"""
    if error_detail.category == ErrorCategory.VALIDATION:
        return 400
    elif error_detail.category == ErrorCategory.AUTHENTICATION:
        return 401
    elif error_detail.category == ErrorCategory.AUTHORIZATION:
        return 403
    elif error_detail.category == ErrorCategory.BUSINESS_LOGIC:
        return 422
    elif error_detail.category in [ErrorCategory.DATABASE, ErrorCategory.SYSTEM]:
        return 500
    elif error_detail.category in [ErrorCategory.CACHE, ErrorCategory.EXTERNAL_API, ErrorCategory.AI_MODEL]:
        return 503
    else:
        return 500

# Error handling decorators
def handle_errors(service_name: str = None):
    """Decorator for handling errors in functions"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)

                # Record success for circuit breaker
                if service_name:
                    error_handler.record_success(service_name)

                return result

            except Exception as e:
                # Extract context if available
                context = _extract_context_from_args(args, kwargs)

                # Handle error
                error_detail = error_handler.handle_exception(e, context)

                # Create response
                return create_error_response(error_detail)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                # Record success for circuit breaker
                if service_name:
                    error_handler.record_success(service_name)

                return result

            except Exception as e:
                # Extract context if available
                context = _extract_context_from_args(args, kwargs)

                # Handle error
                error_detail = error_handler.handle_exception(e, context)

                # Create response
                return create_error_response(error_detail)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

def _extract_context_from_args(args: tuple, kwargs: dict) -> ErrorContext:
    """Extract error context from function arguments"""
    context = ErrorContext()

    # Try to extract request information
    for arg in args:
        if hasattr(arg, 'client'):
            context.ip_address = getattr(arg.client, 'host', None)
        elif hasattr(arg, 'headers'):
            context.user_agent = arg.headers.get('user-agent')
        elif hasattr(arg, 'url'):
            context.endpoint = str(arg.url.path) if hasattr(arg.url, 'path') else str(arg.url)
        elif hasattr(arg, 'method'):
            context.method = arg.method

    # Try to extract user information
    if 'user_id' in kwargs:
        context.user_id = kwargs['user_id']
    elif 'session' in kwargs and hasattr(kwargs['session'], 'user_id'):
        context.user_id = kwargs['session'].user_id

    return context

# Recovery strategies
def register_default_recovery_strategies():
    """Register default recovery strategies"""

    def database_recovery(error_detail: ErrorDetail):
        """Database recovery strategy"""
        logger.info("Attempting database recovery: reconnecting to database")
        # Implementation would depend on database connection management

    def cache_recovery(error_detail: ErrorDetail):
        """Cache recovery strategy"""
        logger.info("Attempting cache recovery: flushing cache")
        # Implementation would clear cache and attempt reconnection

    def external_api_recovery(error_detail: ErrorDetail):
        """External API recovery strategy"""
        logger.info("Attempting external API recovery: using fallback")
        # Implementation would use fallback data or alternative service

    error_handler.register_recovery_strategy("database_DATABASE_ERROR", database_recovery)
    error_handler.register_recovery_strategy("cache_CACHE_ERROR", cache_recovery)
    error_handler.register_recovery_strategy("external_api_EXTERNAL_API_ERROR", external_api_recovery)

# Initialize recovery strategies
register_default_recovery_strategies()

# Export components
__all__ = [
    'ErrorHandler',
    'ErrorDetail',
    'ErrorContext',
    'ErrorSeverity',
    'ErrorCategory',
    'AEGISException',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'DatabaseError',
    'CacheError',
    'ExternalAPIError',
    'AIModelError',
    'SystemError',
    'NetworkError',
    'BusinessLogicError',
    'error_handler',
    'create_error_response',
    'handle_errors'
]