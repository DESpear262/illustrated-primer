"""
Interface Common Module for AI Tutor Proof of Concept.

Provides shared components for GUI interfaces, including the unified backend facade
and common data models.
"""

from src.interface_common.app_facade import AppFacade, get_facade
from src.interface_common.exceptions import (
    FacadeError,
    FacadeTimeoutError,
    FacadeValidationError,
)

__all__ = [
    "AppFacade",
    "get_facade",
    "FacadeError",
    "FacadeTimeoutError",
    "FacadeValidationError",
]

