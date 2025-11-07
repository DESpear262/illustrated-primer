"""
Facade access module for FastAPI application.

Provides facade instance access to avoid circular imports.
"""

from typing import Optional
from src.interface_common.app_facade import AppFacade

# Global facade instance
_facade: Optional[AppFacade] = None


def set_facade(facade_instance: Optional[AppFacade]):
    """
    Set the global facade instance.
    
    Args:
        facade_instance: AppFacade instance or None
    """
    global _facade
    _facade = facade_instance


def get_facade() -> AppFacade:
    """
    Get the global facade instance.
    
    Returns:
        AppFacade instance
        
    Raises:
        RuntimeError: If facade is not initialized
    """
    if _facade is None:
        raise RuntimeError("Facade not initialized")
    return _facade

