"""
Custom exceptions for GUI–Backend Facade.

Provides structured exception classes for different error types that can occur
during GUI-initiated operations. All exceptions are designed to be serializable
for JSON responses.
"""

from typing import Optional, Dict, Any


class FacadeError(Exception):
    """
    Base exception for all facade-related errors.
    
    All facade exceptions inherit from this class and can be serialized
    to dictionaries for JSON responses.
    """
    
    def __init__(self, message: str, error_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize facade error.
        
        Args:
            message: Human-readable error message
            error_type: Optional error type identifier
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize exception to dictionary for JSON responses.
        
        Returns:
            Dictionary with error information
        """
        return {
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
        }


class FacadeTimeoutError(FacadeError):
    """
    Exception raised when an operation times out.
    
    Used for LLM calls, FAISS operations, and other long-running tasks.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, timeout_seconds: Optional[float] = None):
        """
        Initialize timeout error.
        
        Args:
            message: Error message
            operation: Name of the operation that timed out
            timeout_seconds: Timeout value in seconds
        """
        details = {}
        if operation:
            details["operation"] = operation
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        
        super().__init__(message, error_type="TimeoutError", details=details)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class FacadeDatabaseError(FacadeError):
    """
    Exception raised for database-related errors.
    
    Used for database connection failures, query errors, and constraint violations.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, db_path: Optional[str] = None):
        """
        Initialize database error.
        
        Args:
            message: Error message
            operation: Name of the database operation that failed
            db_path: Path to the database file
        """
        details = {}
        if operation:
            details["operation"] = operation
        if db_path:
            details["db_path"] = db_path
        
        super().__init__(message, error_type="DatabaseError", details=details)
        self.operation = operation
        self.db_path = db_path


class FacadeIndexError(FacadeError):
    """
    Exception raised for FAISS index-related errors.
    
    Used for index build failures, search errors, and index file issues.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, index_path: Optional[str] = None):
        """
        Initialize index error.
        
        Args:
            message: Error message
            operation: Name of the index operation that failed
            index_path: Path to the index file
        """
        details = {}
        if operation:
            details["operation"] = operation
        if index_path:
            details["index_path"] = index_path
        
        super().__init__(message, error_type="IndexError", details=details)
        self.operation = operation
        self.index_path = index_path


class FacadeAIError(FacadeError):
    """
    Exception raised for AI service-related errors.
    
    Used for LLM API failures, rate limiting, and model errors.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize AI error.
        
        Args:
            message: Error message
            operation: Name of the AI operation that failed
            model: Model name that was used
        """
        details = {}
        if operation:
            details["operation"] = operation
        if model:
            details["model"] = model
        
        super().__init__(message, error_type="AIError", details=details)
        self.operation = operation
        self.model = model


class FacadeChatError(FacadeError):
    """
    Exception raised for chat-related errors.
    
    Used for session management failures, message processing errors, and chat API issues.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, session_id: Optional[str] = None):
        """
        Initialize chat error.
        
        Args:
            message: Error message
            operation: Name of the chat operation that failed
            session_id: Session ID if applicable
        """
        details = {}
        if operation:
            details["operation"] = operation
        if session_id:
            details["session_id"] = session_id
        
        super().__init__(message, error_type="ChatError", details=details)
        self.operation = operation
        self.session_id = session_id

