"""
Enhanced Error Handling Utilities

Provides graceful error handling and recovery mechanisms.
"""

import logging
import traceback
import functools
from typing import Callable, Any, Optional, Dict
from datetime import datetime


class ErrorHandler:
    """Centralized error handling with logging and recovery."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize error handler.

        Args:
            logger: Logger instance (creates one if not provided)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_history: list = []

    def record_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Record an error with context.

        Args:
            error: The exception that occurred
            context: Additional context information
        """
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        self.error_history.append(error_record)
        self.logger.error(
            f"{error_record['error_type']}: {error_record['error_message']}",
            extra={"context": context}
        )

    def get_error_history(self, limit: int = 10) -> list:
        """
        Get recent error history.

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of recent error records
        """
        return self.error_history[-limit:]

    def clear_history(self) -> None:
        """Clear error history."""
        self.error_history = []


def handle_errors(
    default_return: Any = None,
    log_error: bool = True,
    raise_error: bool = False,
    error_message: str = None
):
    """
    Decorator for handling errors in functions.

    Args:
        default_return: Value to return on error
        log_error: Whether to log the error
        raise_error: Whether to re-raise the error after handling
        error_message: Custom error message

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger = logging.getLogger(func.__module__)
                    msg = error_message or f"Error in {func.__name__}: {str(e)}"
                    logger.error(msg, exc_info=True)

                if raise_error:
                    raise

                return default_return
        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions on error.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger = logging.getLogger(func.__module__)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger = logging.getLogger(func.__module__)
                        logger.error(
                            f"All {max_retries} retry attempts failed for {func.__name__}"
                        )

            # All retries failed
            raise last_exception

        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default: Any = None,
    log_errors: bool = True,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default: Default value to return on error
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or default value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger = logging.getLogger(func.__module__)
            logger.error(f"Error executing {func.__name__}: {str(e)}", exc_info=True)
        return default


class GracefulDegradation:
    """
    Context manager for graceful degradation.

    Usage:
        with GracefulDegradation("feature_name") as gd:
            # Try primary approach
            result = primary_function()

        if gd.failed:
            # Fallback approach
            result = fallback_function()
    """

    def __init__(self, feature_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize graceful degradation context.

        Args:
            feature_name: Name of the feature for logging
            logger: Logger instance
        """
        self.feature_name = feature_name
        self.logger = logger or logging.getLogger(__name__)
        self.failed = False
        self.error = None

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback

        Returns:
            True to suppress exception, False to propagate
        """
        if exc_type is not None:
            self.failed = True
            self.error = exc_val
            self.logger.warning(
                f"Feature '{self.feature_name}' failed gracefully: {str(exc_val)}",
                exc_info=True
            )
            return True  # Suppress exception
        return False


class ErrorRecovery:
    """Error recovery strategies."""

    @staticmethod
    def with_fallback(primary: Callable, fallback: Callable, *args, **kwargs) -> Any:
        """
        Execute primary function with fallback on error.

        Args:
            primary: Primary function to try
            fallback: Fallback function if primary fails
            *args: Arguments for functions
            **kwargs: Keyword arguments for functions

        Returns:
            Result from primary or fallback function
        """
        try:
            return primary(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Primary function failed: {str(e)}. Using fallback.",
                exc_info=True
            )
            return fallback(*args, **kwargs)

    @staticmethod
    def with_default(func: Callable, default: Any, *args, **kwargs) -> Any:
        """
        Execute function with default value on error.

        Args:
            func: Function to execute
            default: Default value on error
            *args: Arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result or default value
        """
        try:
            return func(*args, **kwargs)
        except Exception:
            return default


def validate_input(
    validator: Callable[[Any], bool],
    error_message: str = "Invalid input"
):
    """
    Decorator for input validation.

    Args:
        validator: Function that returns True if input is valid
        error_message: Error message for invalid input

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate first positional argument
            if args and not validator(args[0]):
                raise ValueError(f"{error_message}: {args[0]}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global error handler instance
global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return global_error_handler
