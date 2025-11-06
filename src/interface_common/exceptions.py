"""
Custom exceptions for the GUI-backend facade.

Provides structured error handling for GUI-initiated operations.
"""


class FacadeError(Exception):
    """
    Base exception for all facade errors.
    
    All facade errors inherit from this class for consistent error handling.
    """

    def __init__(self, message: str, details: dict | None = None):
        """
        Initialize facade error.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FacadeTimeoutError(FacadeError):
    """
    Exception raised when an operation exceeds its timeout.
    
    Used for LLM calls, FAISS operations, and other long-running tasks.
    """

    def __init__(self, operation: str, timeout_seconds: float, details: dict | None = None):
        """
        Initialize timeout error.
        
        Args:
            operation: Name of the operation that timed out
            timeout_seconds: Timeout value that was exceeded
            details: Optional dictionary with additional error context
        """
        message = f"Operation '{operation}' timed out after {timeout_seconds}s"
        super().__init__(message, details)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class FacadeValidationError(FacadeError):
    """
    Exception raised when input validation fails.
    
    Used for invalid parameters, missing required fields, etc.
    """

    def __init__(self, field: str, value: any, reason: str, details: dict | None = None):
        """
        Initialize validation error.
        
        Args:
            field: Name of the field that failed validation
            value: The invalid value
            reason: Explanation of why validation failed
            details: Optional dictionary with additional error context
        """
        message = f"Validation failed for '{field}': {reason} (value: {value})"
        super().__init__(message, details)
        self.field = field
        self.value = value
        self.reason = reason

